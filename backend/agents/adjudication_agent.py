"""
Adjudication Agent — the final decision maker.
THIS IS THE ONLY AGENT USING GPT-4o (premium model).
All other agents use gpt-4o-mini.
"""
import json
import asyncio
from backend.agents.base_agent import BaseAgent
from backend.models.claim import (
    ClaimContext, AdjudicationResult, Decision, ClaimStatus, ClaimPriority
)

ADJUDICATION_SYSTEM_PROMPT = """You are the Chief Claims Adjudicator at a leading insurance company.
You make final, legally defensible decisions on insurance claims.

Decision Framework:
APPROVE:
  - Policy is active and claim type is covered
  - All required documents present and valid
  - No fraud indicators (score < 40)
  - Claim within policy limits
  - No exclusions triggered
  - High confidence (> 80%)

REJECT:
  - Policy expired, cancelled, or claim type not covered
  - Confirmed fraud (score > 70) with clear evidence
  - Exclusion clause clearly applies
  - Document fraud confirmed
  - Duplicate claim confirmed

ESCALATE (Human Review Required):
  - Fraud score 40-70 (medium risk — needs human judgment)
  - Confidence < 75% (ambiguous case)
  - Claim amount > ₹10,00,000 (high-value)
  - Missing critical documents but partial information available
  - Complex multi-condition case
  - Borderline exclusion case

PAYOUT CALCULATION:
- Final Payout = min(Claim Amount, Coverage Amount) - Deductible
- Apply sub-limits if applicable (e.g., room rent cap)
- Final payout cannot be negative

Be precise, fair, and provide detailed reasoning that can withstand legal scrutiny.
Return valid JSON only."""

ADJUDICATION_USER_TEMPLATE = """Make a final claims decision based on all available evidence:

CLAIM SUMMARY:
- Claim ID: {claim_id}
- Claim Type: {claim_type}
- Priority: {priority}
- Submitted Amount: ₹{claim_amount}
- Incident Date: {incident_date}
- Claimant: {claimant_name}
- Channel: {channel}

POLICY VALIDATION RESULT:
- Valid: {is_valid}
- Policy Active: {policy_active}
- Claim Type Covered: {claim_type_covered}
- Within Sum Insured: {within_sum_insured}
- Coverage Amount: ₹{coverage_amount}
- Deductible: ₹{deductible}
- Exclusions Hit: {exclusions_hit}
- Validation Notes: {validation_notes}

FRAUD ASSESSMENT:
- Fraud Score: {fraud_score}/100
- Risk Level: {risk_level}
- Flags: {fraud_flags}
- Reasoning: {fraud_reasoning}

MISSING INFORMATION:
- Has Missing Info: {has_missing_info}
- Missing Fields: {missing_fields}

EXTRACTED DOCUMENTS:
{doc_summary}

DESCRIPTION: {description}

Return final decision as JSON:
{{
    "decision": "Approve|Reject|Escalate",
    "claim_amount": 0.00,
    "approved_amount": 0.00,
    "deductible_applied": 0.00,
    "final_payout": 0.00,
    "rationale": "detailed legal-quality rationale (minimum 3 sentences)",
    "confidence_score": 0.95,
    "supporting_evidence": ["evidence point 1", "evidence point 2"],
    "escalation_reason": null,
    "rejection_reason": null,
    "conditions": [],
    "processing_notes": "any special notes for the team"
}}"""


class AdjudicationAgent(BaseAgent):
    def __init__(self):
        super().__init__("AdjudicationAgent")

    async def process(self, context: ClaimContext) -> ClaimContext:
        self.log("adjudication_started", claim_id=context.claim_id)

        # Pre-check: definitive reject before calling expensive model
        pre_decision = self._pre_adjudication_check(context)
        if pre_decision:
            context.adjudication_result = pre_decision
            self._update_status(context)
            context.add_audit(
                agent_name=self.name,
                action="PRE_ADJUDICATION_DECISION",
                details={"decision": pre_decision.decision.value, "reason": "Rule-based pre-check"},
            )
            return context

        if self.settings.demo_mode:
            return await self._demo_adjudicate(context)

        try:
            return await self._llm_adjudicate(context)
        except Exception as e:
            self.log_error("adjudication_llm_failed", error=str(e))
            return await self._demo_adjudicate(context)

    def _pre_adjudication_check(self, context: ClaimContext) -> AdjudicationResult | None:
        validation = context.validation_result
        fraud = context.fraud_result

        # Definitive reject: policy not active
        if validation and not validation.policy_active:
            return AdjudicationResult(
                decision=Decision.REJECT,
                claim_amount=context.submission.claim_amount,
                approved_amount=0.0,
                deductible_applied=0.0,
                final_payout=0.0,
                rationale=(
                    "Claim rejected: The insurance policy is not active on the incident date. "
                    "Coverage is only valid between the policy start and end dates. "
                    "Customer should contact the agent to renew or reinstate the policy."
                ),
                confidence_score=1.0,
                supporting_evidence=["Policy validation confirmed inactive status"],
                rejection_reason="Policy expired or not yet active",
            )

        # Definitive escalate: very high fraud score
        if fraud and fraud.fraud_score >= self.settings.fraud_escalation_threshold:
            return AdjudicationResult(
                decision=Decision.ESCALATE,
                claim_amount=context.submission.claim_amount,
                approved_amount=0.0,
                deductible_applied=0.0,
                final_payout=0.0,
                rationale=(
                    f"Claim escalated for mandatory human review due to high fraud risk score of "
                    f"{fraud.fraud_score}/100. Specific fraud indicators: {', '.join(fraud.flags[:3])}. "
                    "A senior adjudicator must review this claim before any decision is made."
                ),
                confidence_score=0.9,
                supporting_evidence=fraud.flags,
                escalation_reason=f"High fraud risk: score {fraud.fraud_score}/100",
            )

        # Definitive escalate: very high value
        if context.submission.claim_amount > self.settings.high_value_escalation_amount:
            return AdjudicationResult(
                decision=Decision.ESCALATE,
                claim_amount=context.submission.claim_amount,
                approved_amount=0.0,
                deductible_applied=0.0,
                final_payout=0.0,
                rationale=(
                    f"Claim amount ₹{context.submission.claim_amount:,.0f} exceeds the automatic "
                    f"adjudication threshold of ₹{self.settings.high_value_escalation_amount:,.0f}. "
                    "High-value claims require senior adjudicator approval per company policy."
                ),
                confidence_score=0.95,
                supporting_evidence=[f"Claim amount ₹{context.submission.claim_amount:,.0f} > threshold"],
                escalation_reason="High-value claim requires senior adjudicator review",
            )

        return None

    async def _llm_adjudicate(self, context: ClaimContext) -> ClaimContext:
        validation = context.validation_result
        fraud = context.fraud_result
        missing = context.missing_info_result

        doc_summary = {
            d.get("doc_type"): {
                k: v for k, v in d.get("normalized_fields", {}).items()
                if k not in ["tables"]
            }
            for d in context.extracted_documents
        }

        user_msg = ADJUDICATION_USER_TEMPLATE.format(
            claim_id=context.claim_id,
            claim_type=context.claim_type.value if context.claim_type else "Unknown",
            priority=context.priority.value,
            claim_amount=context.submission.claim_amount,
            incident_date=context.submission.incident_date,
            claimant_name=context.submission.claimant.name,
            channel=context.submission.channel.value,
            is_valid=validation.is_valid if validation else "Unknown",
            policy_active=validation.policy_active if validation else "Unknown",
            claim_type_covered=validation.claim_type_covered if validation else "Unknown",
            within_sum_insured=validation.within_sum_insured if validation else "Unknown",
            coverage_amount=validation.coverage_amount if validation else 0,
            deductible=validation.deductible_amount if validation else 0,
            exclusions_hit=validation.exclusions_hit if validation else [],
            validation_notes=validation.validation_notes if validation else "",
            fraud_score=fraud.fraud_score if fraud else 0,
            risk_level=fraud.risk_level if fraud else "LOW",
            fraud_flags=fraud.flags if fraud else [],
            fraud_reasoning=fraud.reasoning if fraud else "",
            has_missing_info=missing.has_missing_info if missing else False,
            missing_fields=missing.missing_fields if missing else [],
            doc_summary=json.dumps(doc_summary, indent=2)[:2000],
            description=context.submission.description,
        )

        # GPT-4o ONLY HERE — this is the expensive model call
        raw = await self.call_llm(
            messages=[
                {"role": "system", "content": ADJUDICATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            model=self.settings.gpt4o_deployment,  # GPT-4o
            response_format={"type": "json_object"},
            temperature=0.05,  # Very low temperature for consistent decisions
        )
        result = json.loads(raw)

        decision_str = result.get("decision", "Escalate")
        decision = Decision(decision_str)

        context.adjudication_result = AdjudicationResult(
            decision=decision,
            claim_amount=float(result.get("claim_amount", context.submission.claim_amount)),
            approved_amount=float(result.get("approved_amount", 0)),
            deductible_applied=float(result.get("deductible_applied", 0)),
            final_payout=float(result.get("final_payout", 0)),
            rationale=result.get("rationale", ""),
            confidence_score=float(result.get("confidence_score", 0.8)),
            supporting_evidence=result.get("supporting_evidence", []),
            escalation_reason=result.get("escalation_reason"),
            rejection_reason=result.get("rejection_reason"),
        )

        self._update_status(context)
        context.add_audit(
            agent_name=self.name,
            action="ADJUDICATION_COMPLETE",
            details={
                "decision": decision.value,
                "payout": context.adjudication_result.final_payout,
                "confidence": context.adjudication_result.confidence_score,
                "model_used": "gpt-4o",
            },
        )
        self.log("adjudication_complete", claim_id=context.claim_id, decision=decision.value)
        return context

    async def _demo_adjudicate(self, context: ClaimContext) -> ClaimContext:
        await asyncio.sleep(0.5)

        validation = context.validation_result
        fraud = context.fraud_result
        missing = context.missing_info_result

        claim_amount = context.submission.claim_amount
        coverage = validation.coverage_amount if validation else claim_amount
        deductible = validation.deductible_amount if validation else 0

        # Determine decision based on all signals
        if validation and not validation.is_valid:
            decision = Decision.REJECT
            payout = 0.0
            rationale = (
                f"Claim rejected based on policy validation: {validation.validation_notes} "
                "The policy terms do not support this claim as submitted. "
                "Customer may appeal this decision within 30 days."
            )
            rejection_reason = validation.validation_notes
            escalation_reason = None
        elif fraud and fraud.fraud_score >= 40:
            decision = Decision.ESCALATE
            payout = 0.0
            rationale = (
                f"Claim escalated for human review due to fraud risk score of {fraud.fraud_score}/100. "
                f"Specific concerns: {'; '.join(fraud.flags[:2]) if fraud.flags else 'anomalies detected'}. "
                "A senior adjudicator will review and respond within 2 business days."
            )
            escalation_reason = f"Fraud risk score: {fraud.fraud_score}/100"
            rejection_reason = None
        elif missing and missing.has_missing_info and len(missing.missing_fields) > 2:
            decision = Decision.ESCALATE
            payout = 0.0
            rationale = (
                "Claim escalated as critical documents are missing for proper adjudication. "
                f"Missing: {', '.join(missing.missing_fields[:3])}. "
                "Follow-up has been sent to the claimant. Claim will be reassessed upon receipt."
            )
            escalation_reason = f"Missing critical documents: {', '.join(missing.missing_fields[:2])}"
            rejection_reason = None
        else:
            decision = Decision.APPROVE
            payout = max(min(claim_amount, coverage) - deductible, 0)
            rationale = (
                f"Claim approved after thorough validation. Policy is active, claim type is covered, "
                f"and no fraud indicators were detected (fraud score: {fraud.fraud_score if fraud else 0}/100). "
                f"Coverage amount ₹{coverage:,.0f} less deductible ₹{deductible:,.0f} = "
                f"final payout ₹{payout:,.0f}. Payment will be initiated within 3 business days."
            )
            escalation_reason = None
            rejection_reason = None

        confidence = 0.92 if decision == Decision.APPROVE else 0.87

        context.adjudication_result = AdjudicationResult(
            decision=decision,
            claim_amount=claim_amount,
            approved_amount=coverage if decision == Decision.APPROVE else 0.0,
            deductible_applied=deductible if decision == Decision.APPROVE else 0.0,
            final_payout=payout,
            rationale=rationale,
            confidence_score=confidence,
            supporting_evidence=[
                f"Policy validated: {validation.policy_active if validation else 'N/A'}",
                f"Fraud score: {fraud.fraud_score if fraud else 0}/100",
                f"Documents processed: {len(context.extracted_documents)}",
            ],
            escalation_reason=escalation_reason,
            rejection_reason=rejection_reason,
        )
        self._update_status(context)
        context.add_audit(
            agent_name=self.name,
            action="ADJUDICATION_COMPLETE",
            details={
                "decision": decision.value,
                "payout": payout,
                "confidence": confidence,
                "model_used": "demo",
            },
        )
        return context

    def _update_status(self, context: ClaimContext):
        decision = context.adjudication_result.decision
        if decision == Decision.APPROVE:
            context.status = ClaimStatus.APPROVED
        elif decision == Decision.REJECT:
            context.status = ClaimStatus.REJECTED
        else:
            context.status = ClaimStatus.UNDER_REVIEW
