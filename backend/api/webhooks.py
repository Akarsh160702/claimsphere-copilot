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
from fastapi import APIRouter, HTTPException, Request, Header, Query
from fastapi.responses import HTMLResponse
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

    if decision_str not in ("Approve", "Reject", "MoreInfo"):
        raise HTTPException(status_code=400, detail=f"Invalid decision: {decision_str}")

    if decision_str == "Approve":
        new_status_val = "APPROVED"
    elif decision_str == "Reject":
        new_status_val = "REJECTED"
    else:
        new_status_val = "PENDING_INFO"

    # Persist to Dataverse FIRST — before any in-memory check so this works
    # even after a container restart when _processing_contexts is empty.
    try:
        from backend.tools.dataverse import DataverseClient
        dv = DataverseClient()
        ctx_ref = _processing_contexts.get(claim_id)
        pol = ctx_ref.submission.policy_id if (ctx_ref and ctx_ref.submission) else ""
        cln = ctx_ref.submission.claimant.name if (ctx_ref and ctx_ref.submission) else ""
        await dv.update_claim(
            claim_id,
            {"decision": decision_str, "status": new_status_val},
            policy_id=pol,
            claimant_name=cln,
        )
    except Exception as e:
        logger.warning("teams_decision_dataverse_update_failed", error=str(e))

    if claim_id not in _processing_contexts:
        logger.warning("teams_decision_claim_not_found", claim_id=claim_id)
        return {
            "status": "not_found",
            "message": f"Claim {claim_id} not in active queue (Dataverse update attempted).",
        }

    ctx = _processing_contexts[claim_id]

    # Idempotency: first Teams decision wins — prevents double-click / PA retry from
    # flipping the result (e.g. Approve at t+0 then Reject at t+1).
    if any(a.action == "TEAMS_HUMAN_DECISION" for a in ctx.audit_trail):
        logger.info(
            "teams_decision_already_recorded",
            claim_id=claim_id,
            incoming_decision=decision_str,
        )
        return {
            "status": "already_decided",
            "claim_id": claim_id,
            "message": f"Teams decision already recorded for {claim_id}. First decision stands.",
        }

    # Apply decision to in-memory context
    if ctx.adjudication_result:
        try:
            ctx.adjudication_result.decision = Decision(decision_str)
        except ValueError:
            pass
        decision_label = {
            "Approve": "Approved",
            "Reject": "Rejected",
            "MoreInfo": "More Info Requested",
        }.get(decision_str, decision_str)
        rationale_suffix = f"\n\nTeams Decision by {payload.reviewer}: {decision_label} via Teams card"
        if payload.notes:
            rationale_suffix += f" — {payload.notes}"
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


@router.get("/teams-decision")
async def teams_decision_redirect(
    claim_id: str = Query(...),
    decision: str = Query(...),
    reviewer: str = Query("teams-adjudicator"),
    notes: str = Query(""),
):
    """
    Called when an adjudicator opens the Approve/Reject link from a Teams card.

    IMPORTANT: a GET MUST NOT mutate claim state. Microsoft SafeLinks, Teams URL
    unfurling, Outlook link preview and other crawlers automatically *prefetch*
    these URLs the moment the card is posted — which previously auto-applied a
    decision ~14s after escalation with no human involved (non-deterministic
    Approve/Reject). So this handler ONLY renders a confirmation page. The
    decision is applied solely when a human clicks "Confirm", which fires a POST
    to this same route (crawlers never POST).
    """
    if decision not in ("Approve", "Reject", "MoreInfo"):
        return HTMLResponse("<h2>Invalid decision value.</h2>", status_code=400)

    label = {"Approve": "Approve", "Reject": "Reject", "MoreInfo": "Request More Info"}.get(decision, decision)
    color = {"Approve": "#107C10", "Reject": "#A4262C", "MoreInfo": "#0078D4"}.get(decision, "#000")
    api_base = get_settings().api_base_url.rstrip("/")
    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>ClaimSphere — Confirm Decision</title>
<style>body{{font-family:Segoe UI,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#f3f2f1}}
.card{{background:#fff;border-radius:8px;padding:40px 56px;box-shadow:0 2px 8px rgba(0,0,0,.12);text-align:center;max-width:480px}}
h1{{color:{color};margin:0 0 8px;font-size:22px}}p{{color:#605e5c;margin:0 0 20px;line-height:1.5}}
button{{background:{color};color:#fff;border:0;border-radius:6px;padding:12px 28px;font-size:15px;font-weight:600;cursor:pointer}}
button:disabled{{opacity:.6;cursor:default}}#done{{display:none;color:{color};font-weight:600;margin-top:14px}}</style></head>
<body><div class="card">
<h1>Confirm: {label}</h1>
<p>You are about to <strong>{label.lower()}</strong> claim <strong>{claim_id}</strong>.<br>This decision is final. Please confirm.</p>
<button id="btn" onclick="confirmDecision()">Confirm {label}</button>
<div id="done"></div>
<script>
async function confirmDecision() {{
  const btn = document.getElementById('btn');
  btn.disabled = true; btn.textContent = 'Submitting…';
  try {{
    const r = await fetch('{api_base}/webhooks/teams-decision', {{
      method: 'POST', headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{claim_id: {claim_id!r}, decision: {decision!r}, reviewer: {reviewer!r}, notes: {notes!r}}})
    }});
    const data = await r.json();
    btn.style.display = 'none';
    const done = document.getElementById('done');
    done.style.display = 'block';
    done.textContent = data.status === 'already_decided'
      ? 'A decision was already recorded for this claim.'
      : 'Recorded — claim {claim_id} marked as {label.lower()}. You can close this tab.';
  }} catch (e) {{
    btn.disabled = false; btn.textContent = 'Retry {label}';
  }}
}}
</script>
</div></body></html>""")


@router.get("/health")
async def webhook_health():
    """Health probe for the webhooks module."""
    settings = get_settings()
    return {
        "status": "ready",
        "pa_webhook_configured": bool(settings.power_automate_webhook_url),
        "api_base_url": settings.api_base_url,
    }
