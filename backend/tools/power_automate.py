"""
Power Automate integration — fires HTTP webhooks for Teams notifications.

Flow:
  ClaimOrchestrator → power_automate.notify_escalation()
      → POST to Power Automate HTTP trigger
      → PA flow posts Adaptive Card to Teams channel
      → Adjudicator clicks button in Teams
      → PA calls back POST /webhooks/teams-decision
      → ClaimDetail reflects decision in real time

Falls back silently when POWER_AUTOMATE_WEBHOOK_URL is not configured
(demo mode / local dev) so the pipeline never breaks.
"""
import aiohttp
import structlog
from datetime import datetime

logger = structlog.get_logger()

FRONTEND_BASE = "https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io"


def _build_escalation_payload(
    claim_id: str,
    claim_type: str,
    claimant_name: str,
    claimant_email: str,
    amount: float,
    escalation_reason: str,
    fraud_score: int,
    confidence_pct: int,
    ai_recommendation: str,
    callback_url: str,
) -> dict:
    """
    Builds the JSON payload sent to the Power Automate HTTP trigger.
    PA parses this and constructs the Teams Adaptive Card.
    The `actions` list drives the actionable buttons in Teams — each
    button POSTs back to `callback_url` (our /webhooks/teams-decision).
    """
    return {
        "claim_id": claim_id,
        "claim_type": claim_type,
        "claimant_name": claimant_name,
        "claimant_email": claimant_email,
        "amount_inr": round(amount),
        "escalation_reason": escalation_reason,
        "fraud_score": fraud_score,
        "confidence_pct": confidence_pct,
        "ai_recommendation": ai_recommendation,
        "escalated_at": datetime.utcnow().isoformat() + "Z",
        "review_url": f"{FRONTEND_BASE}/claims/{claim_id}",
        # These are forwarded verbatim by the PA flow as the card action URLs
        "callback_approve": f"{callback_url}?claim_id={claim_id}&decision=Approve",
        "callback_reject":  f"{callback_url}?claim_id={claim_id}&decision=Reject",
        "callback_info":    f"{callback_url}?claim_id={claim_id}&decision=MoreInfo",
        # Inline adaptive card so PA can pass it directly to Teams
        "adaptive_card": _build_adaptive_card(
            claim_id=claim_id,
            claim_type=claim_type,
            claimant_name=claimant_name,
            amount=amount,
            escalation_reason=escalation_reason,
            fraud_score=fraud_score,
            confidence_pct=confidence_pct,
            ai_recommendation=ai_recommendation,
            callback_url=callback_url,
        ),
    }


def _build_adaptive_card(
    claim_id: str,
    claim_type: str,
    claimant_name: str,
    amount: float,
    escalation_reason: str,
    fraud_score: int,
    confidence_pct: int,
    ai_recommendation: str,
    callback_url: str,
) -> dict:
    """
    Microsoft Adaptive Card v1.4 — compatible with Teams and Copilot Studio.
    Power Automate posts this via the 'Post adaptive card in a chat or channel' action.
    """
    fraud_color = (
        "Good" if fraud_score < 30 else "Warning" if fraud_score < 60 else "Attention"
    )
    rec_color = (
        "Good" if "approv" in ai_recommendation.lower()
        else "Attention" if "reject" in ai_recommendation.lower()
        else "Warning"
    )

    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "items": [
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [
                                    {
                                        "type": "Image",
                                        "url": "https://adaptivecards.io/content/pending.png",
                                        "size": "Small",
                                        "altText": "Pending review",
                                    }
                                ],
                            },
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": "ClaimSphere — Human Review Required",
                                        "weight": "Bolder",
                                        "size": "Medium",
                                        "wrap": True,
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"Claim **{claim_id}** requires your adjudication",
                                        "spacing": "None",
                                        "wrap": True,
                                        "isSubtle": True,
                                    },
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Claim ID",      "value": claim_id},
                    {"title": "Type",          "value": claim_type},
                    {"title": "Claimant",      "value": claimant_name},
                    {"title": "Amount",        "value": f"₹{amount:,.0f}"},
                    {
                        "title": "Fraud Score",
                        "value": f"{fraud_score}/100 — **{fraud_color.upper()}**",
                    },
                    {
                        "title": "AI Confidence",
                        "value": f"{confidence_pct}%",
                    },
                    {
                        "title": "AI Recommendation",
                        "value": ai_recommendation,
                    },
                    {"title": "Escalation Reason", "value": escalation_reason},
                ],
            },
            {
                "type": "TextBlock",
                "text": "Select your decision below. This will update ClaimSphere in real time.",
                "wrap": True,
                "isSubtle": True,
                "spacing": "Medium",
            },
        ],
        "actions": [
            {
                "type": "Action.Http",
                "title": "Approve",
                "method": "POST",
                "url": f"{callback_url}",
                "body": f'{{"claim_id": "{claim_id}", "decision": "Approve", "reviewer": "teams-adjudicator"}}',
                "headers": [{"name": "Content-Type", "value": "application/json"}],
                "style": "positive",
            },
            {
                "type": "Action.Http",
                "title": "Reject",
                "method": "POST",
                "url": f"{callback_url}",
                "body": f'{{"claim_id": "{claim_id}", "decision": "Reject", "reviewer": "teams-adjudicator"}}',
                "headers": [{"name": "Content-Type", "value": "application/json"}],
                "style": "destructive",
            },
            {
                "type": "Action.Http",
                "title": "Request More Info",
                "method": "POST",
                "url": f"{callback_url}",
                "body": f'{{"claim_id": "{claim_id}", "decision": "MoreInfo", "reviewer": "teams-adjudicator"}}',
                "headers": [{"name": "Content-Type", "value": "application/json"}],
            },
            {
                "type": "Action.OpenUrl",
                "title": "Open in ClaimSphere",
                "url": f"{FRONTEND_BASE}/claims/{claim_id}",
            },
        ],
    }


async def notify_escalation(
    claim_id: str,
    claim_type: str,
    claimant_name: str,
    claimant_email: str,
    amount: float,
    escalation_reason: str,
    fraud_score: int,
    confidence_score: float,
    ai_recommendation: str,
    webhook_url: str,
    callback_base_url: str,
) -> bool:
    """
    POST escalation payload to Power Automate HTTP trigger.
    Returns True on success, False on any failure (never raises).
    """
    if not webhook_url:
        logger.info("pa_webhook_skipped", reason="POWER_AUTOMATE_WEBHOOK_URL not configured")
        return False

    callback_url = f"{callback_base_url}/webhooks/teams-decision"
    payload = _build_escalation_payload(
        claim_id=claim_id,
        claim_type=claim_type,
        claimant_name=claimant_name,
        claimant_email=claimant_email,
        amount=amount,
        escalation_reason=escalation_reason,
        fraud_score=fraud_score,
        confidence_pct=round(confidence_score * 100),
        ai_recommendation=ai_recommendation,
        callback_url=callback_url,
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status in (200, 202):
                    logger.info(
                        "pa_escalation_notified",
                        claim_id=claim_id,
                        status=resp.status,
                    )
                    return True
                else:
                    body = await resp.text()
                    logger.warning(
                        "pa_webhook_non_200",
                        claim_id=claim_id,
                        status=resp.status,
                        body=body[:200],
                    )
                    return False
    except Exception as e:
        logger.error("pa_webhook_failed", claim_id=claim_id, error=str(e))
        return False


async def notify_decision(
    claim_id: str,
    decision: str,
    claimant_name: str,
    payout: float,
    webhook_url: str,
) -> bool:
    """
    POST final decision notification (Approve/Reject) to Power Automate.
    PA can use this to update Teams thread or send claimant email via M365.
    """
    if not webhook_url:
        return False

    payload = {
        "event": "claim_decided",
        "claim_id": claim_id,
        "decision": decision,
        "claimant_name": claimant_name,
        "payout_inr": round(payout),
        "decided_at": datetime.utcnow().isoformat() + "Z",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                logger.info("pa_decision_notified", claim_id=claim_id, decision=decision, status=resp.status)
                return resp.status in (200, 202)
    except Exception as e:
        logger.error("pa_decision_notify_failed", claim_id=claim_id, error=str(e))
        return False
