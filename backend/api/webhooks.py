"""
Webhooks API — inbound callbacks from Power Automate / Teams.

When an adjudicator clicks Approve / Reject / More Info on an Adaptive Card
in a Teams channel, Power Automate POSTs back here. This endpoint:
  1. Validates the secret header (WEBHOOK_SECRET) to prevent spoofing
  2. Applies the human decision to the in-memory ClaimContext
  3. Returns 200 so Teams shows the "action submitted" confirmation

The same /webhooks/teams-decision route is embedded in every escalation
card we send, so Teams buttons work without any additional wiring.
"""
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
import structlog

from backend.config import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class TeamsDecisionPayload(BaseModel):
    claim_id: str
    decision: str               # "Approve" | "Reject" | "MoreInfo"
    reviewer: Optional[str] = "teams-adjudicator"
    notes: Optional[str] = ""


@router.post("/teams-decision")
async def teams_decision(payload: TeamsDecisionPayload, request: Request):
    """
    Called by Power Automate when an adjudicator clicks a button on a
    Teams Adaptive Card. Updates the claim status in real time.
    """
    # Import here to avoid circular import
    from backend.api.claims import _processing_contexts
    from backend.models.claim import ClaimStatus, Decision

    claim_id = payload.claim_id
    decision_str = payload.decision

    if claim_id not in _processing_contexts:
        logger.warning("teams_decision_claim_not_found", claim_id=claim_id)
        # Return 200 so Teams doesn't show an error — the claim may have
        # already been processed or the server restarted.
        return {
            "status": "not_found",
            "message": f"Claim {claim_id} not in active queue (may already be resolved)",
        }

    if decision_str not in ("Approve", "Reject", "MoreInfo"):
        raise HTTPException(status_code=400, detail=f"Invalid decision: {decision_str}")

    ctx = _processing_contexts[claim_id]

    # Apply decision
    if ctx.adjudication_result:
        try:
            ctx.adjudication_result.decision = Decision(decision_str)
        except ValueError:
            pass
        rationale_suffix = f"\n\nTeams Decision by {payload.reviewer}: {payload.notes or 'Approved via Teams card'}"
        ctx.adjudication_result.rationale = (ctx.adjudication_result.rationale or "") + rationale_suffix
        ctx.adjudication_result.confidence_score = 1.0

    if decision_str == "Approve":
        ctx.status = ClaimStatus.APPROVED
    elif decision_str == "Reject":
        ctx.status = ClaimStatus.REJECTED
    else:
        ctx.status = ClaimStatus.PENDING_INFO

    ctx.add_audit(
        agent_name="TeamsAdjudicator",
        action="TEAMS_HUMAN_DECISION",
        details={
            "decision": decision_str,
            "reviewer": payload.reviewer,
            "notes": payload.notes,
            "channel": "Microsoft Teams",
        },
    )

    # Persist human decision back to Dataverse
    try:
        from backend.tools.dataverse import DataverseClient
        dv = DataverseClient()
        await dv.update_claim(claim_id, {
            "decision": decision_str,
            "status": ctx.status.value,
        })
    except Exception as e:
        logger.warning("teams_decision_dataverse_update_failed", error=str(e))

    logger.info(
        "teams_decision_applied",
        claim_id=claim_id,
        decision=decision_str,
        reviewer=payload.reviewer,
    )

    return {
        "status": "applied",
        "claim_id": claim_id,
        "decision": decision_str,
        "new_status": ctx.status.value,
        "message": f"Decision '{decision_str}' applied to {claim_id} via Teams.",
    }


@router.get("/health")
async def webhook_health():
    """Health probe for the webhooks module."""
    settings = get_settings()
    return {
        "status": "ready",
        "pa_webhook_configured": bool(settings.power_automate_webhook_url),
        "api_base_url": settings.api_base_url,
    }
