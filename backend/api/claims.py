from functools import lru_cache
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.models.claim import (
    ClaimSubmission, ClaimResponse, ClaimStatusResponse,
    ClaimContext, ClaimStatus
)
from backend.orchestrator import ClaimOrchestrator

router = APIRouter(prefix="/claims", tags=["Claims"])

@lru_cache(maxsize=1)
def _get_orchestrator() -> ClaimOrchestrator:
    return ClaimOrchestrator()

def get_orchestrator() -> ClaimOrchestrator:
    return _get_orchestrator()

# In-memory registry for async processing results
_processing_contexts: dict[str, ClaimContext] = {}


@router.post("/submit", response_model=ClaimResponse)
async def submit_claim(submission: ClaimSubmission, background_tasks: BackgroundTasks):
    """Submit a new insurance claim for processing."""
    context = ClaimContext(submission=submission)
    claim_id = context.claim_id

    _processing_contexts[claim_id] = context

    background_tasks.add_task(_process_claim_async, claim_id, submission)

    return ClaimResponse(
        claim_id=claim_id,
        status=ClaimStatus.RECEIVED,
        message=f"Claim received and processing started. Track at /claims/{claim_id}/status",
        tracking_url=f"/claims/{claim_id}/status",
    )


@router.post("/submit/sync", response_model=dict)
async def submit_claim_sync(submission: ClaimSubmission):
    """Submit claim and wait for complete processing (for demo purposes)."""
    context = await get_orchestrator().process_claim(submission)
    _processing_contexts[context.claim_id] = context
    return context.model_dump(mode="json")


@router.get("/{claim_id}/status", response_model=dict)
async def get_claim_status(claim_id: str):
    """Get current status of a claim."""
    # Check in-memory first (fastest)
    if claim_id in _processing_contexts:
        ctx = _processing_contexts[claim_id]
        return {
            "claim_id": ctx.claim_id,
            "status": ctx.status.value,
            "claim_type": ctx.claim_type.value if ctx.claim_type else None,
            "priority": ctx.priority.value,
            "submitted_at": ctx.created_at.isoformat(),
            "updated_at": ctx.updated_at.isoformat(),
            "adjudication": ctx.adjudication_result.model_dump() if ctx.adjudication_result else None,
            "missing_info": ctx.missing_info_result.model_dump() if ctx.missing_info_result else None,
            "fraud_summary": f"Score: {ctx.fraud_result.fraud_score}/100, Risk: {ctx.fraud_result.risk_level}" if ctx.fraud_result else None,
            "audit_trail_count": len(ctx.audit_trail),
        }

    # Fall back to Dataverse
    claim = await get_orchestrator().get_claim_status(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    return claim


@router.get("/{claim_id}/full", response_model=dict)
async def get_claim_full(claim_id: str):
    """Get full claim context including all agent outputs."""
    if claim_id in _processing_contexts:
        return _processing_contexts[claim_id].model_dump(mode="json")
    raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found in active context")


@router.get("/", response_model=list)
async def list_claims():
    """List all processed claims."""
    all_claims = await get_orchestrator().get_all_claims()
    # Merge with in-memory
    in_memory = [
        {
            "claim_id": ctx.claim_id,
            "status": ctx.status.value,
            "claim_type": ctx.claim_type.value if ctx.claim_type else None,
            "claim_amount": ctx.submission.claim_amount,
            "claimant_name": ctx.submission.claimant.name,
            "submitted_at": ctx.created_at.isoformat(),
            "decision": ctx.adjudication_result.decision.value if ctx.adjudication_result else None,
            "final_payout": ctx.adjudication_result.final_payout if ctx.adjudication_result else None,
            "fraud_score": ctx.fraud_result.fraud_score if ctx.fraud_result else None,
            "channel": ctx.submission.channel.value if ctx.submission.channel else "Web",
        }
        for ctx in _processing_contexts.values()
    ]
    if not all_claims:
        return in_memory
    return in_memory or all_claims


@router.post("/{claim_id}/human-decision", response_model=dict)
async def record_human_decision(claim_id: str, decision: dict):
    """Record a human adjudicator's decision on an escalated claim."""
    if claim_id not in _processing_contexts:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

    ctx = _processing_contexts[claim_id]
    human_decision = decision.get("decision", "Approve")
    notes = decision.get("notes", "Human adjudicator decision")
    adjuster_id = decision.get("adjuster_id", "human-adjudicator")

    if ctx.adjudication_result:
        from backend.models.claim import Decision
        ctx.adjudication_result.decision = Decision(human_decision)
        ctx.adjudication_result.rationale += f"\n\nHuman Override by {adjuster_id}: {notes}"
        ctx.adjudication_result.confidence_score = 1.0

    if human_decision == "Approve":
        ctx.status = ClaimStatus.APPROVED
    elif human_decision == "Reject":
        ctx.status = ClaimStatus.REJECTED
    else:
        ctx.status = ClaimStatus.PENDING_INFO

    ctx.add_audit(
        agent_name="HumanAdjudicator",
        action="HUMAN_DECISION",
        details={"decision": human_decision, "notes": notes, "adjuster": adjuster_id},
    )
    return {"claim_id": claim_id, "decision": human_decision, "status": ctx.status.value}


async def _process_claim_async(claim_id: str, submission: ClaimSubmission):
    context = await get_orchestrator().process_claim(submission)
    _processing_contexts[claim_id] = context
