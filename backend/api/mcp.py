"""
ClaimSphere MCP Server — Model Context Protocol over HTTP + SSE
Spec: https://modelcontextprotocol.io  (protocol version 2025-03-26)

Exposes ClaimSphere as MCP tools consumable by:
  - Copilot Studio (Actions → Model Context Protocol)
  - Claude Desktop / VS Code Copilot Agent
  - Any MCP-compatible AI assistant

Transport:
  POST /mcp   — Streamable HTTP (request/response JSON-RPC)
  GET  /mcp/sse        — SSE transport: open stream, receive endpoint event
  POST /mcp/messages   — SSE transport: send JSON-RPC, receive via SSE
"""

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/mcp", tags=["MCP"])

# ---------------------------------------------------------------------------
# In-memory SSE session store  {session_id: asyncio.Queue}
# ---------------------------------------------------------------------------
_sessions: dict[str, asyncio.Queue] = {}

# ---------------------------------------------------------------------------
# Tool definitions (MCP schema)
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "submit_claim",
        "description": (
            "Submit a new insurance claim for AI-powered processing. "
            "Returns a claim_id you can use to track progress."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["claimant_name", "policy_id", "claim_type", "amount", "description"],
            "properties": {
                "claimant_name": {"type": "string", "description": "Full name of the claimant"},
                "policy_id": {"type": "string", "description": "Policy ID (e.g. POL-HEALTH-001)"},
                "claim_type": {
                    "type": "string",
                    "enum": ["health", "motor", "property", "travel"],
                    "description": "Type of insurance claim",
                },
                "amount": {"type": "number", "description": "Claimed amount in INR"},
                "description": {"type": "string", "description": "Description of the incident"},
                "hospital_name": {"type": "string", "description": "Hospital name (health claims)"},
                "diagnosis": {"type": "string", "description": "Medical diagnosis (health claims)"},
            },
        },
    },
    {
        "name": "get_claim_status",
        "description": "Get the current processing status, AI decision, and fraud score for a claim.",
        "inputSchema": {
            "type": "object",
            "required": ["claim_id"],
            "properties": {
                "claim_id": {
                    "type": "string",
                    "description": "Claim ID returned by submit_claim (e.g. CLM-20260606-3DE38D)",
                },
            },
        },
    },
    {
        "name": "search_policy",
        "description": (
            "Search the policy database to check coverage, limits, exclusions, "
            "deductibles, and premium details."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language query e.g. 'cardiac surgery coverage' or policy ID",
                },
                "policy_id": {
                    "type": "string",
                    "description": "Specific policy ID to look up (optional)",
                },
            },
        },
    },
    {
        "name": "check_coverage",
        "description": "Ask whether a specific treatment, procedure, or event is covered under a policy.",
        "inputSchema": {
            "type": "object",
            "required": ["policy_id", "question"],
            "properties": {
                "policy_id": {"type": "string"},
                "question": {
                    "type": "string",
                    "description": "e.g. 'Is knee replacement surgery covered?'",
                },
            },
        },
    },
    {
        "name": "list_claims",
        "description": "List recent claims with their status. Useful for getting an overview of the pipeline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max number of claims to return (default 10)",
                    "default": 10,
                },
                "status_filter": {
                    "type": "string",
                    "description": "Filter by status: pending, approved, rejected, escalated, processing",
                },
            },
        },
    },
    {
        "name": "get_fraud_score",
        "description": "Get the AI fraud analysis and risk score for a submitted claim.",
        "inputSchema": {
            "type": "object",
            "required": ["claim_id"],
            "properties": {
                "claim_id": {"type": "string"},
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

async def _call_tool(name: str, args: dict) -> list[dict]:
    """Execute a tool and return MCP content list."""
    try:
        if name == "get_claim_status":
            return await _tool_get_claim_status(args)
        if name == "submit_claim":
            return await _tool_submit_claim(args)
        if name == "search_policy":
            return await _tool_search_policy(args)
        if name == "check_coverage":
            return await _tool_check_coverage(args)
        if name == "list_claims":
            return await _tool_list_claims(args)
        if name == "get_fraud_score":
            return await _tool_get_fraud_score(args)
        return [{"type": "text", "text": f"Unknown tool: {name}"}]
    except Exception as exc:
        logger.warning("mcp_tool_error", tool=name, error=str(exc))
        return [{"type": "text", "text": f"Tool error: {exc}"}]


async def _tool_get_claim_status(args: dict) -> list[dict]:
    from backend.api.claims import _processing_contexts
    claim_id = args["claim_id"]
    ctx = _processing_contexts.get(claim_id)
    if not ctx:
        return [{"type": "text", "text": f"Claim {claim_id} not found. It may be in a different backend instance. Try submitting a new claim via submit_claim tool."}]
    data = {
        "claim_id": ctx.claim_id,
        "status": str(ctx.status.value) if hasattr(ctx.status, "value") else str(ctx.status),
        "decision": str(ctx.final_decision.value) if hasattr(ctx.final_decision, "value") else str(ctx.final_decision) if ctx.final_decision else None,
        "priority": str(ctx.priority.value) if hasattr(ctx.priority, "value") else str(ctx.priority),
        "fraud_score": ctx.fraud_score,
        "claim_type": str(ctx.claim_type.value) if hasattr(ctx.claim_type, "value") else str(ctx.claim_type) if ctx.claim_type else None,
        "submitted_at": ctx.created_at.isoformat() if hasattr(ctx.created_at, "isoformat") else str(ctx.created_at),
    }
    return [{"type": "text", "text": json.dumps(data, indent=2, default=str)}]


async def _tool_submit_claim(args: dict) -> list[dict]:
    from backend.models.claim import ClaimSubmission
    from backend.api.claims import _processing_contexts, get_orchestrator
    sub = ClaimSubmission(
        claimant_name=args["claimant_name"],
        policy_id=args["policy_id"],
        claim_type=args["claim_type"],
        amount=args["amount"],
        description=args["description"],
        hospital_name=args.get("hospital_name"),
        diagnosis=args.get("diagnosis"),
    )
    orchestrator = get_orchestrator()
    ctx = await orchestrator.process_claim(sub)
    _processing_contexts[ctx.claim_id] = ctx
    result = {
        "claim_id": ctx.claim_id,
        "status": ctx.status.value,
        "decision": ctx.final_decision,
        "fraud_score": ctx.fraud_score,
        "message": f"Claim processed. Track at /claims/{ctx.claim_id}/status",
    }
    return [{"type": "text", "text": json.dumps(result, indent=2)}]


async def _tool_search_policy(args: dict) -> list[dict]:
    try:
        from backend.tools.ai_search import AISearchClient
        client = AISearchClient()
        query = args.get("query", args.get("policy_id", ""))
        results = await client.search_policies(query)
        return [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]
    except Exception:
        from backend.tools.ai_search import POLICY_DATABASE
        query = args.get("query", "").lower()
        pid = args.get("policy_id", "").upper()
        matches = []
        for p in POLICY_DATABASE:
            if pid and p.get("policy_id") == pid:
                matches = [p]
                break
            if query and (query in str(p).lower()):
                matches.append(p)
        return [{"type": "text", "text": json.dumps(matches[:5], indent=2, default=str)}]


async def _tool_check_coverage(args: dict) -> list[dict]:
    try:
        from backend.tools.ai_search import POLICY_DATABASE
        pid = args["policy_id"].upper()
        question = args["question"]
        policy = next((p for p in POLICY_DATABASE if p.get("policy_id") == pid), None)
        if not policy:
            return [{"type": "text", "text": f"Policy {pid} not found."}]
        answer = {
            "policy_id": pid,
            "question": question,
            "covered_treatments": policy.get("covered_treatments", []),
            "exclusions": policy.get("exclusions", []),
            "sum_insured": policy.get("sum_insured"),
            "deductible": policy.get("deductible"),
            "guidance": (
                "Check covered_treatments and exclusions above. "
                "For definitive answers consult the policy document."
            ),
        }
        return [{"type": "text", "text": json.dumps(answer, indent=2, default=str)}]
    except Exception as exc:
        return [{"type": "text", "text": str(exc)}]


async def _tool_list_claims(args: dict) -> list[dict]:
    from backend.api.claims import _processing_contexts
    limit = int(args.get("limit", 10))
    status_filter = args.get("status_filter", "").lower()
    claims = []
    for ctx in list(_processing_contexts.values()):
        if status_filter and ctx.status.value.lower() != status_filter:
            continue
        claims.append({
            "claim_id": ctx.claim_id,
            "status": ctx.status.value,
            "decision": ctx.final_decision,
            "amount": ctx.submission.amount if ctx.submission else None,
            "claim_type": ctx.claim_type.value if ctx.claim_type else None,
            "fraud_score": ctx.fraud_score,
            "submitted_at": ctx.created_at.isoformat(),
        })
    claims.sort(key=lambda c: c["submitted_at"], reverse=True)
    return [{"type": "text", "text": json.dumps(claims[:limit], indent=2, default=str)}]


async def _tool_get_fraud_score(args: dict) -> list[dict]:
    from backend.api.claims import _processing_contexts
    claim_id = args["claim_id"]
    ctx = _processing_contexts.get(claim_id)
    if not ctx:
        return [{"type": "text", "text": f"Claim {claim_id} not found."}]
    data = {
        "claim_id": ctx.claim_id,
        "fraud_score": ctx.fraud_score,
        "fraud_flags": getattr(ctx, "fraud_flags", []),
        "risk_level": (
            "HIGH" if (ctx.fraud_score or 0) >= 70
            else "MEDIUM" if (ctx.fraud_score or 0) >= 40
            else "LOW"
        ),
    }
    return [{"type": "text", "text": json.dumps(data, indent=2, default=str)}]


# ---------------------------------------------------------------------------
# JSON-RPC dispatch
# ---------------------------------------------------------------------------

def _ok(req_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


async def _dispatch(msg: dict) -> dict | None:
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "ClaimSphere Copilot", "version": "1.0.0"},
            "instructions": (
                "ClaimSphere Copilot exposes AI-powered insurance claims processing. "
                "Use submit_claim to file a claim, get_claim_status to track it, "
                "search_policy for coverage details, and list_claims for an overview."
            ),
        })

    if method == "notifications/initialized":
        return None  # notification, no response

    if method == "ping":
        return _ok(req_id, {})

    if method == "tools/list":
        return _ok(req_id, {"tools": _TOOLS})

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        if not tool_name:
            return _err(req_id, -32602, "Missing tool name")
        content = await _call_tool(tool_name, tool_args)
        return _ok(req_id, {"content": content, "isError": False})

    if method == "resources/list":
        return _ok(req_id, {"resources": []})

    if method == "prompts/list":
        return _ok(req_id, {"prompts": []})

    return _err(req_id, -32601, f"Method not found: {method}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", summary="MCP Streamable HTTP transport")
async def mcp_post(request: Request):
    """
    MCP Streamable HTTP transport (spec 2025-03-26).
    Accepts JSON-RPC 2.0 request or batch array.
    Returns JSON-RPC 2.0 response.
    """
    body = await request.json()

    # Batch support
    if isinstance(body, list):
        results = [r for r in [await _dispatch(m) for m in body] if r is not None]
        return JSONResponse(content=results)

    result = await _dispatch(body)
    if result is None:
        return JSONResponse(content={}, status_code=202)
    return JSONResponse(content=result)


@router.get("/sse", summary="MCP SSE transport — open stream")
async def mcp_sse(request: Request):
    """
    MCP SSE transport: open a persistent SSE connection.
    The server immediately sends an `endpoint` event with the POST URL.
    """
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _sessions[session_id] = queue

    # Derive base URL from the request so this works in any environment
    base = str(request.base_url).rstrip("/")
    messages_url = f"{base}/mcp/messages?session_id={session_id}"

    async def event_stream():
        try:
            # Immediately tell the client where to POST messages
            yield f"event: endpoint\ndata: {messages_url}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    payload = json.dumps(msg)
                    yield f"event: message\ndata: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            _sessions.pop(session_id, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/messages", summary="MCP SSE transport — send message")
async def mcp_messages(session_id: str, request: Request):
    """Receive JSON-RPC from client; push response onto the SSE queue."""
    queue = _sessions.get(session_id)
    if queue is None:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    body = await request.json()
    result = await _dispatch(body)
    if result is not None:
        await queue.put(result)
    return JSONResponse(content={}, status_code=202)


@router.get("", summary="MCP server info")
async def mcp_info():
    """Human-readable discovery endpoint — returns server metadata and tool list."""
    return {
        "server": "ClaimSphere Copilot MCP Server",
        "version": "1.0.0",
        "protocol": "2025-03-26",
        "team": "NEXORA — LTM x Microsoft Hack2Future 2026",
        "transports": {
            "streamable_http": "POST /mcp",
            "sse": {"stream": "GET /mcp/sse", "messages": "POST /mcp/messages"},
        },
        "tools": [{"name": t["name"], "description": t["description"]} for t in _TOOLS],
    }
