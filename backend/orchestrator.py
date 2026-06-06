"""
Claim Orchestrator — coordinates all agents in the processing pipeline.

Pipeline:
  RouterAgent → DocumentAgent → [ValidationAgent + FraudAgent in parallel]
  → MissingInfoAgent → AdjudicationAgent → Notifications
"""
import asyncio
from datetime import datetime
import structlog

from backend.models.claim import ClaimContext, ClaimSubmission, ClaimStatus
from backend.agents.router_agent import RouterAgent
from backend.agents.document_agent import DocumentAgent
from backend.agents.validation_agent import ValidationAgent
from backend.agents.missing_info_agent import MissingInfoAgent
from backend.agents.fraud_agent import FraudAgent
from backend.agents.adjudication_agent import AdjudicationAgent
from backend.tools.dataverse import DataverseClient
from backend.tools.mock_integrations import MockNotificationClient, MockPaymentClient
from backend.tools.power_automate import notify_escalation, notify_decision
from backend.config import get_settings

logger = structlog.get_logger()


class ClaimOrchestrator:
    def __init__(self):
        self.settings = get_settings()
        self.router = RouterAgent()
        self.document_processor = DocumentAgent()
        self.validator = ValidationAgent()
        self.missing_info_checker = MissingInfoAgent()
        self.fraud_detector = FraudAgent()
        self.adjudicator = AdjudicationAgent()
        self.dataverse = DataverseClient()
        self.notifier = MockNotificationClient()
        self.payment = MockPaymentClient()

    async def process_claim(self, submission: ClaimSubmission) -> ClaimContext:
        context = ClaimContext(submission=submission)
        logger.info("claim_processing_started", claim_id=context.claim_id)

        try:
            context = await self._run_pipeline(context)
        except Exception as e:
            logger.error("pipeline_error", claim_id=context.claim_id, error=str(e))
            context.error = str(e)
            context.status = ClaimStatus.ESCALATED

        # Persist final state
        await self._persist_context(context)

        # Send notifications
        await self._send_notifications(context)

        logger.info(
            "claim_processing_complete",
            claim_id=context.claim_id,
            status=context.status.value,
            decision=context.adjudication_result.decision.value if context.adjudication_result else "N/A",
        )
        return context

    async def _run_pipeline(self, context: ClaimContext) -> ClaimContext:
        # Stage 1: Route and classify
        context = await self.router.process(context)
        await self._save_progress(context)

        # Stage 2: Extract documents
        context = await self.document_processor.process(context)
        await self._save_progress(context)

        # Stage 3: Validation + Fraud Detection in PARALLEL (saves time)
        context = await self._parallel_validation_fraud(context)
        await self._save_progress(context)

        # Stage 4: Missing information check
        context = await self.missing_info_checker.process(context)
        await self._save_progress(context)

        # Stage 5: Final adjudication
        context = await self.adjudicator.process(context)

        return context

    async def _parallel_validation_fraud(self, context: ClaimContext) -> ClaimContext:
        """Run validation and fraud detection in parallel for speed."""
        validation_ctx = context.model_copy(deep=True)
        fraud_ctx = context.model_copy(deep=True)

        validation_result, fraud_result = await asyncio.gather(
            self.validator.process(validation_ctx),
            self.fraud_detector.process(fraud_ctx),
            return_exceptions=True,
        )

        if isinstance(validation_result, Exception):
            logger.error("validation_parallel_failed", error=str(validation_result))
        else:
            context.validation_result = validation_result.validation_result
            context.policy_data = validation_result.policy_data
            for entry in validation_result.audit_trail:
                if entry.agent_name == "ValidationAgent":
                    context.audit_trail.append(entry)

        if isinstance(fraud_result, Exception):
            logger.error("fraud_parallel_failed", error=str(fraud_result))
        else:
            context.fraud_result = fraud_result.fraud_result
            for entry in fraud_result.audit_trail:
                if entry.agent_name == "FraudAgent":
                    context.audit_trail.append(entry)

        return context

    async def _save_progress(self, context: ClaimContext):
        try:
            await self.dataverse.update_claim(
                context.claim_id,
                {
                    "status": context.status.value,
                    "updated_at": datetime.utcnow().isoformat(),
                    "claim_type": context.claim_type.value if context.claim_type else None,
                    "priority": context.priority.value,
                },
            )
        except Exception as e:
            logger.warning("progress_save_failed", error=str(e))

    async def _persist_context(self, context: ClaimContext):
        try:
            claim_record = {
                "claim_id": context.claim_id,
                "policy_id": context.submission.policy_id,
                "claim_type": context.claim_type.value if context.claim_type else "Unknown",
                "status": context.status.value,
                "claimant_name": context.submission.claimant.name,
                "claimant_email": context.submission.claimant.email,
                "claim_amount": context.submission.claim_amount,
                "incident_date": context.submission.incident_date,
                "channel": context.submission.channel.value,
                "priority": context.priority.value,
                "fraud_score": context.fraud_result.fraud_score if context.fraud_result else 0,
                "fraud_risk_level": context.fraud_result.risk_level if context.fraud_result else "LOW",
                "decision": context.adjudication_result.decision.value if context.adjudication_result else None,
                "approved_amount": context.adjudication_result.approved_amount if context.adjudication_result else 0,
                "final_payout": context.adjudication_result.final_payout if context.adjudication_result else 0,
                "rationale": context.adjudication_result.rationale if context.adjudication_result else None,
                "confidence_score": context.adjudication_result.confidence_score if context.adjudication_result else 0,
                "stp_flag": context.status in (ClaimStatus.APPROVED, ClaimStatus.REJECTED),
                "escalated": context.status == ClaimStatus.UNDER_REVIEW,
                "created_at": context.created_at.isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "description": context.submission.description,
            }
            await self.dataverse.create_claim(claim_record)

            for doc in context.extracted_documents:
                await self.dataverse.create_document_record({
                    **doc,
                    "claim_id": context.claim_id,
                })

            for audit in context.audit_trail:
                await self.dataverse.create_audit_log({
                    "claim_id": context.claim_id,
                    "agent_name": audit.agent_name,
                    "action": audit.action,
                    "timestamp": audit.timestamp.isoformat(),
                    "details": str(audit.details),
                })
        except Exception as e:
            logger.error("context_persist_failed", error=str(e))

    async def _send_notifications(self, context: ClaimContext):
        try:
            claimant = context.submission.claimant
            decision = context.adjudication_result.decision.value if context.adjudication_result else "Processing"

            if context.status == ClaimStatus.APPROVED:
                payout = context.adjudication_result.final_payout
                subject = f"Claim {context.claim_id} — Approved ✓"
                body = (
                    f"Dear {claimant.name},\n\n"
                    f"Your insurance claim {context.claim_id} has been APPROVED.\n"
                    f"Approved Amount: ₹{context.adjudication_result.approved_amount:,.0f}\n"
                    f"Deductible Applied: ₹{context.adjudication_result.deductible_applied:,.0f}\n"
                    f"Final Payout: ₹{payout:,.0f}\n\n"
                    f"Payment will be credited to your registered bank account within 3 business days.\n\n"
                    f"Claim Reference: {context.claim_id}\n\n"
                    f"Thank you for choosing ClaimSphere Insurance.\n\nRegards,\nClaimSphere Claims Team"
                )
                # Initiate payout for approved claims
                await self.payment.initiate_payout(
                    context.claim_id, payout, claimant.name
                )

            elif context.status == ClaimStatus.REJECTED:
                reason = context.adjudication_result.rejection_reason or "Policy terms not met"
                subject = f"Claim {context.claim_id} — Decision Update"
                body = (
                    f"Dear {claimant.name},\n\n"
                    f"After thorough review, your claim {context.claim_id} could not be approved.\n\n"
                    f"Reason: {reason}\n\n"
                    f"You have the right to appeal this decision within 30 days by contacting "
                    f"our Claims Review Team at claims@claimsphere.demo\n\n"
                    f"Regards,\nClaimSphere Claims Team"
                )

            elif context.status == ClaimStatus.UNDER_REVIEW:
                reason = context.adjudication_result.escalation_reason if context.adjudication_result else "Complex case"
                subject = f"Claim {context.claim_id} — Under Review"
                body = (
                    f"Dear {claimant.name},\n\n"
                    f"Your claim {context.claim_id} has been escalated for expert review.\n"
                    f"A senior claims adjudicator will assess your claim within 2 business days.\n\n"
                    f"You will receive an update via email. For urgent queries, call 1800-XXX-XXXX.\n\n"
                    f"Regards,\nClaimSphere Claims Team"
                )

                # Fire Teams notification via Power Automate (real integration)
                adj = context.adjudication_result
                await notify_escalation(
                    claim_id=context.claim_id,
                    claim_type=context.claim_type.value if context.claim_type else "Unknown",
                    claimant_name=claimant.name,
                    claimant_email=claimant.email,
                    amount=context.submission.claim_amount,
                    escalation_reason=reason,
                    fraud_score=context.fraud_result.fraud_score if context.fraud_result else 0,
                    confidence_score=adj.confidence_score if adj else 0.0,
                    ai_recommendation=adj.decision.value if adj else "Escalate",
                    webhook_url=self.settings.power_automate_webhook_url,
                    callback_base_url=self.settings.api_base_url,
                )

            elif context.status == ClaimStatus.PENDING_INFO:
                missing = context.missing_info_result
                subject = f"Claim {context.claim_id} — Additional Information Required"
                body = missing.follow_up_message if missing else (
                    f"Dear {claimant.name},\n\nWe need additional documents for claim {context.claim_id}.\n"
                    f"Please contact us at 1800-XXX-XXXX."
                )
            else:
                return

            await self.notifier.send_email(
                to=claimant.email,
                subject=subject,
                body=body,
            )
        except Exception as e:
            logger.error("notification_failed", error=str(e))

    async def get_claim_status(self, claim_id: str) -> dict:
        return await self.dataverse.get_claim(claim_id)

    async def get_all_claims(self) -> list[dict]:
        return await self.dataverse.get_all_claims()
