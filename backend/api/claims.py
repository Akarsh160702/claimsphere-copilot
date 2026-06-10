from functools import lru_cache
from fastapi import APIRouter, HTTPException, BackgroundTasks
import structlog
from backend.models.claim import (
    ClaimSubmission, ClaimResponse, ClaimStatusResponse,
    ClaimContext, ClaimStatus
)
from backend.orchestrator import ClaimOrchestrator

router = APIRouter(prefix="/claims", tags=["Claims"])
logger = structlog.get_logger()

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
        
    # Map raw/mapped Dataverse record to the status model schema
    if "claim_id" in claim:
        status_val = claim.get("status", "Processing")
        decision = claim.get("decision")
        claim_amount = claim.get("claim_amount", 0.0)
        approved_amount = claim.get("final_payout", 0.0)
        rationale = claim.get("rationale") or ""
        fraud_score = claim.get("fraud_score", 0)
        
        risk_level = "LOW"
        if fraud_score >= 60:
            risk_level = "HIGH"
        elif fraud_score >= 30:
            risk_level = "MEDIUM"

        has_missing = status_val == "Pending Information"
        missing_fields = ["Supporting Documents"] if has_missing else []

        return {
            "claim_id": claim["claim_id"],
            "status": status_val,
            "claim_type": claim.get("claim_type"),
            "priority": claim.get("priority", "Medium"),
            "submitted_at": claim.get("submitted_at"),
            "updated_at": claim.get("updated_at"),
            "adjudication": {
                "decision": decision or "Escalate",
                "claim_amount": claim_amount,
                "approved_amount": approved_amount,
                "deductible_applied": max(0.0, claim_amount - approved_amount),
                "final_payout": approved_amount,
                "rationale": rationale,
                "confidence_score": 0.95,
                "supporting_evidence": []
            },
            "missing_info": {
                "has_missing_info": has_missing,
                "missing_fields": missing_fields,
                "follow_up_message": f"Please upload missing documents for claim {claim_id}."
            },
            "fraud_summary": f"Score: {fraud_score}/100, Risk: {risk_level}",
            "audit_trail_count": 0,
        }
    return claim


@router.get("/{claim_id}/full", response_model=dict)
async def get_claim_full(claim_id: str):
    """Get full claim context including all agent outputs."""
    if claim_id in _processing_contexts:
        return _processing_contexts[claim_id].model_dump(mode="json")
        
    # Fallback: retrieve from Dataverse and reconstruct standard ClaimContext structure
    try:
        from backend.tools.dataverse import DataverseClient
        dv = DataverseClient()
        claim_data = await dv.get_claim(claim_id)
        if claim_data:
            docs = await dv.get_claim_documents(claim_id)
            audits = await dv.get_claim_audit_logs(claim_id)
            
            status = claim_data.get("status", "Processing")
            decision = claim_data.get("decision")
            fraud_score = claim_data.get("fraud_score", 0)
            approved_amount = claim_data.get("final_payout", 0.0)
            claim_amount = claim_data.get("claim_amount", 0.0)
            rationale = claim_data.get("rationale") or ""
            
            risk_level = "LOW"
            if fraud_score >= 60:
                risk_level = "HIGH"
            elif fraud_score >= 30:
                risk_level = "MEDIUM"
                
            has_missing = status == "Pending Information"
            missing_fields = ["Supporting Documents"] if has_missing else []
            
            return {
                "claim_id": claim_id,
                "status": status,
                "claim_type": claim_data.get("claim_type", "Health"),
                "priority": claim_data.get("priority", "Medium"),
                "created_at": claim_data.get("submitted_at"),
                "updated_at": claim_data.get("updated_at"),
                "submission": {
                    "policy_id": claim_data.get("policy_id"),
                    "claimant": {
                        "name": claim_data.get("claimant_name"),
                        "email": claim_data.get("claimant_email"),
                        "phone": ""
                    },
                    "claim_type": claim_data.get("claim_type"),
                    "claim_amount": claim_amount,
                    "incident_date": claim_data.get("incident_date"),
                    "description": claim_data.get("description"),
                    "channel": claim_data.get("channel", "Web")
                },
                "validation_result": {
                    "is_valid": decision != "Reject",
                    "policy_active": True,
                    "claim_type_covered": True,
                    "within_sum_insured": True,
                    "deductible_applicable": True,
                    "coverage_amount": claim_amount,
                    "deductible_amount": max(0.0, claim_amount - approved_amount),
                    "validation_notes": rationale,
                    "confidence": 0.95
                },
                "fraud_result": {
                    "fraud_score": fraud_score,
                    "risk_level": risk_level,
                    "flags": [],
                    "reasoning": rationale
                },
                "missing_info_result": {
                    "has_missing_info": has_missing,
                    "missing_fields": missing_fields,
                    "follow_up_message": f"Please upload missing documents for claim {claim_id}."
                },
                "adjudication_result": {
                    "decision": decision or "Escalate",
                    "claim_amount": claim_amount,
                    "approved_amount": approved_amount,
                    "deductible_applied": max(0.0, claim_amount - approved_amount),
                    "final_payout": approved_amount,
                    "rationale": rationale,
                    "confidence_score": 0.95,
                    "supporting_evidence": []
                },
                "extracted_documents": docs,
                "audit_trail": audits
            }
    except Exception as e:
        logger.error("get_claim_full_fallback_failed", claim_id=claim_id, error=str(e))
        
    raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found in active context or Dataverse")


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
        
    # Map/merge lists using claim_id to avoid duplicates
    merged = {c["claim_id"]: c for c in all_claims}
    for c in in_memory:
        merged[c["claim_id"]] = c
        
    return list(merged.values())


@router.post("/{claim_id}/human-decision", response_model=dict)
async def record_human_decision(claim_id: str, decision: dict):
    """Record a human adjudicator's decision on an escalated claim."""
    human_decision = decision.get("decision", "Approve")
    notes = decision.get("notes", "Human adjudicator decision")
    adjuster_id = (
        decision.get("adjuster_id")
        or decision.get("reviewer")
        or "human-adjudicator"
    )

    if human_decision not in ("Approve", "Reject", "MoreInfo"):
        raise HTTPException(status_code=400, detail=f"Invalid decision: {human_decision}")

    if human_decision == "Approve":
        new_status = ClaimStatus.APPROVED
    elif human_decision == "Reject":
        new_status = ClaimStatus.REJECTED
    else:
        new_status = ClaimStatus.PENDING_INFO

    async def _sync_dataverse(
        decision_value: str,
        status_value: str,
        ctx: ClaimContext | None = None,
    ) -> bool:
        try:
            from backend.tools.dataverse import DataverseClient
            dv = DataverseClient()
            return await dv.update_claim(
                claim_id,
                {"decision": decision_value, "status": status_value},
                policy_id=ctx.submission.policy_id if (ctx and ctx.submission) else "",
                claimant_name=ctx.submission.claimant.name if (ctx and ctx.submission) else "",
            )
        except Exception as e:
            logger.warning("human_decision_dataverse_update_failed", claim_id=claim_id, error=str(e))
            return False

    if claim_id not in _processing_contexts:
        dataverse_updated = await _sync_dataverse(human_decision, new_status.value)
        return {
            "claim_id": claim_id,
            "decision": human_decision,
            "status": new_status.value,
            "dataverse_updated": dataverse_updated,
            "note": "not_in_active_context",
        }

    ctx = _processing_contexts[claim_id]

    if ctx.adjudication_result:
        from backend.models.claim import Decision
        try:
            ctx.adjudication_result.decision = Decision(human_decision)
        except ValueError:
            pass
        ctx.adjudication_result.rationale = (
            f"{ctx.adjudication_result.rationale or ''}\n\n"
            f"Human Override by {adjuster_id}: {notes}"
        )
        ctx.adjudication_result.confidence_score = 1.0

    ctx.status = new_status

    ctx.add_audit(
        agent_name="HumanAdjudicator",
        action="HUMAN_DECISION",
        details={"decision": human_decision, "notes": notes, "adjuster": adjuster_id},
    )
    dataverse_updated = await _sync_dataverse(human_decision, ctx.status.value, ctx)
    return {
        "claim_id": claim_id,
        "decision": human_decision,
        "status": ctx.status.value,
        "dataverse_updated": dataverse_updated,
    }


async def _process_claim_async(claim_id: str, submission: ClaimSubmission):
    context = await get_orchestrator().process_claim(submission, claim_id=claim_id)
    _processing_contexts[claim_id] = context
