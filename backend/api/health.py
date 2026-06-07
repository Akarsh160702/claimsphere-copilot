from fastapi import APIRouter
from datetime import datetime
from backend.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    settings = get_settings()
    integrations = await _check_integrations(settings)
    overall = "healthy" if all(v["ok"] for v in integrations.values()) else "degraded"
    return {
        "status": overall,
        "service": "ClaimSphere Copilot API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "demo_mode": settings.demo_mode,
        "team": "NEXORA",
        "hackathon": "LTM x Microsoft Hack2Future 2026",
        "integrations": integrations,
        "mcp_endpoint": "/mcp",
        "docs": "/docs",
    }


async def _check_integrations(settings) -> dict:
    results = {}

    # Azure OpenAI — ok if endpoint is set (key optional; managed identity used in Azure)
    results["azure_openai"] = {
        "ok": bool(settings.azure_openai_endpoint),
        "endpoint": settings.azure_openai_endpoint or "not configured",
        "auth": "api-key" if settings.azure_openai_api_key else "managed-identity",
    }

    # Azure AI Search — ok if endpoint is set (key optional; managed identity used in Azure)
    results["ai_search"] = {
        "ok": bool(settings.search_endpoint),
        "endpoint": settings.search_endpoint or "not configured",
        "index": settings.search_index_name,
        "auth": "api-key" if settings.search_admin_key else "managed-identity",
    }

    # Azure Blob Storage
    results["blob_storage"] = {
        "ok": bool(settings.storage_connection_string or settings.storage_blob_endpoint),
        "container": settings.storage_container_name,
    }

    # Dataverse — attempt a real API call to verify connectivity
    dv_ok = False
    dv_note = "not configured"
    if settings.dataverse_url and settings.dataverse_client_id and settings.dataverse_client_secret:
        try:
            from backend.tools.dataverse import DataverseClient
            client = DataverseClient()
            token = await client._get_token()
            import aiohttp
            base = settings.dataverse_url.rstrip("/")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base}/api/data/v9.2/crcce_claims?$top=1",
                    headers=client._headers(token),
                ) as resp:
                    body = await resp.json()
                    if resp.status == 200:
                        dv_ok = True
                        dv_note = f"live — {len(body.get('value', []))} rows"
                    else:
                        # Discover entity names — list all, filter for claim-related
                        async with session.get(
                            f"{base}/api/data/v9.2/EntityDefinitions"
                            "?$select=LogicalName,EntitySetName&$top=200",
                            headers=client._headers(token),
                        ) as meta_resp:
                            meta = await meta_resp.json()
                            all_sets = [
                                e.get("EntitySetName", "")
                                for e in meta.get("value", [])
                            ]
                            claim_sets = [s for s in all_sets if "claim" in s.lower()]
                        dv_note = (
                            f"HTTP {resp.status}: crcce_claims not found. "
                            f"Claim entities: {claim_sets or 'none'} | "
                            f"Total entities: {len(all_sets)}"
                        )
        except Exception as e:
            dv_note = str(e)[:120]
    results["dataverse"] = {
        "ok": dv_ok,
        "url": settings.dataverse_url or "not configured",
        "note": dv_note,
    }

    # Power Automate / Teams
    results["power_automate"] = {
        "ok": bool(settings.power_automate_webhook_url),
        "configured": bool(settings.power_automate_webhook_url),
    }

    # Document Intelligence — ok if endpoint is set (key optional; managed identity used in Azure)
    results["document_intelligence"] = {
        "ok": bool(settings.doc_intelligence_endpoint),
        "endpoint": settings.doc_intelligence_endpoint or "not configured",
        "auth": "api-key" if settings.doc_intelligence_key else "managed-identity",
    }

    # Application Insights
    results["application_insights"] = {
        "ok": bool(settings.applicationinsights_connection_string),
        "configured": bool(settings.applicationinsights_connection_string),
    }

    # MCP Server
    results["mcp_server"] = {
        "ok": True,
        "endpoint": "/mcp",
        "tools": 6,
        "protocol": "2025-03-26",
    }

    return results


@router.get("/health/dataverse-claim-test")
async def dataverse_claim_test():
    """Call create_claim exactly as the orchestrator does and return the raw outcome."""
    from backend.tools.dataverse import DataverseClient
    import traceback
    client = DataverseClient()
    test_data = {
        "claim_id": "CLM-ORCHTEST-001",
        "policy_id": "POL-HEALTH-001",
        "claim_type": "Health",
        "status": "APPROVED",
        "claimant_name": "Test Claimant",
        "claimant_email": "test@claimsphere.ai",
        "claim_amount": 500000.0,
        "incident_date": "2026-06-07",
        "channel": "WEB",
        "priority": "HIGH",
        "fraud_score": 15,
        "fraud_risk_level": "LOW",
        "decision": "APPROVED",
        "approved_amount": 400000.0,
        "final_payout": 400000.0,
        "rationale": "Test rationale",
        "confidence_score": 0.85,
        "stp_flag": False,
        "escalated": False,
        "description": "Orchestrator test claim",
    }
    try:
        result = await client.create_claim(test_data)
        return {"result": result, "in_demo_store": "CLM-ORCHTEST-001" in __import__('backend.tools.dataverse', fromlist=['_demo_store']).__dict__.get('_demo_store', {})}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@router.get("/health/persist-errors")
async def persist_errors():
    """Return the last 10 persist errors (orchestrator + Dataverse write failures)."""
    from backend.orchestrator import _persist_errors
    from backend.tools.dataverse import _dv_errors
    return {
        "orchestrator_errors": list(_persist_errors),
        "dataverse_write_errors": list(_dv_errors),
    }


@router.get("/health/dataverse-write")
async def dataverse_write_test():
    """Return actual column names for crcce_claim entity from Dataverse metadata."""
    settings = get_settings()
    if not (settings.dataverse_url and settings.dataverse_client_id and settings.dataverse_client_secret):
        return {"error": "Dataverse not configured"}
    try:
        import aiohttp
        from backend.tools.dataverse import DataverseClient
        client = DataverseClient()
        token = await client._get_token()
        base = settings.dataverse_url.rstrip("/")
        async with aiohttp.ClientSession() as session:
            # 1. Discover the primary name attribute (the claim-number column)
            async with session.get(
                f"{base}/api/data/v9.2/EntityDefinitions(LogicalName='crcce_claim')"
                "?$select=PrimaryNameAttribute",
                headers=client._headers(token),
            ) as meta_resp:
                meta = await meta_resp.json()
                primary = meta.get("PrimaryNameAttribute", "crcce_name")

            # 2. Build a record using the discovered primary column
            test_record = {
                primary:               "CLM-TEST-WRITE",
                "crcce_policyid":      "POL-TEST-001",
                "crcce_claimantname":  "Health Check Test",
                "crcce_claimantemail": "test@claimsphere.ai",
                "crcce_claimamount":   500000.0,
                "crcce_approvedamount":400000.0,
                "crcce_fraudscore":    15.0,
                "crcce_incidentdate":  "2026-06-07T00:00:00Z",
                "crcce_rationale":     "Automated write test",
                "crcce_description":   "[Health] Status: APPROVED | Write test",
            }
            async with session.post(
                f"{base}/api/data/v9.2/crcce_claims",
                json=test_record,
                headers=client._headers(token),
            ) as resp:
                body = await resp.text()
                return {
                    "primary_name_attribute": primary,
                    "status": resp.status,
                    "body": body[:600],
                }
    except Exception as e:
        return {"error": str(e)}


@router.get("/")
async def root():
    return {
        "service": "ClaimSphere Copilot",
        "description": "AI-powered end-to-end insurance claims processing",
        "team": "NEXORA — LTM x Microsoft Hack2Future 2026",
        "docs": "/docs",
        "health": "/health",
        "mcp": "/mcp",
    }
