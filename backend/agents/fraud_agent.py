import json
import asyncio
from datetime import datetime
from backend.agents.base_agent import BaseAgent
from backend.models.claim import ClaimContext, FraudResult

FRAUD_SYSTEM_PROMPT = """You are an expert insurance fraud analyst with deep knowledge of fraud patterns.

Your task is to analyze a claim for potential fraud indicators and provide a risk score.

Fraud Score Scale:
0-30: LOW RISK — Proceed with normal processing
31-60: MEDIUM RISK — Proceed with extra scrutiny
61-100: HIGH RISK — Mandatory human review required

Common Fraud Patterns to check:
1. Policy inception fraud: Claim within 30 days of policy start
2. Round number fraud: Claim amount exactly equals policy limit
3. Document fraud: Inconsistencies in dates, amounts, signatures
4. Duplicate claim: Same incident claimed multiple times
5. Suspicious timing: Claim filed immediately after premium payment
6. Exaggerated damages: Claimed amount disproportionate to incident
7. Address fraud: Claimant/incident address inconsistencies
8. Frequency fraud: Multiple claims in short period

Be analytical. Base your assessment on facts. Provide specific flags with evidence.
Return JSON only."""

FRAUD_USER_TEMPLATE = """Analyze this claim for fraud risk:

CLAIM DETAILS:
- Claim ID: {claim_id}
- Policy ID: {policy_id}
- Claim Type: {claim_type}
- Claim Amount: ₹{claim_amount}
- Sum Insured: ₹{sum_insured}
- Amount/Limit Ratio: {ratio:.1%}
- Policy Start Date: {policy_start}
- Incident Date: {incident_date}
- Days Since Policy Start: {days_since_start}
- Description: {description}
- Channel: {channel}

EXTRACTED DOCUMENT DATA:
{document_summary}

POLICY HISTORY:
{claim_history}

Return fraud assessment:
{{
    "fraud_score": 0-100,
    "risk_level": "LOW|MEDIUM|HIGH",
    "flags": ["specific flag 1", "specific flag 2"],
    "reasoning": "detailed explanation of assessment",
    "recommended_action": "proceed|scrutinize|manual_review",
    "specific_checks": {{
        "inception_fraud": false,
        "round_number_fraud": false,
        "document_inconsistency": false,
        "duplicate_claim": false,
        "exaggerated_damages": false
    }}
}}"""


def _days_between(date1_str: str, date2_str: str) -> int:
    try:
        d1 = datetime.strptime(date1_str[:10], "%Y-%m-%d")
        d2 = datetime.strptime(date2_str[:10], "%Y-%m-%d")
        return abs((d2 - d1).days)
    except Exception:
        return 999


class FraudAgent(BaseAgent):
    def __init__(self):
        super().__init__("FraudAgent")

    async def process(self, context: ClaimContext) -> ClaimContext:
        self.log("fraud_check_started", claim_id=context.claim_id)

        rule_flags, rule_score = self._run_rule_checks(context)

        if self.settings.demo_mode:
            return await self._demo_fraud_check(context, rule_flags, rule_score)

        try:
            return await self._llm_fraud_check(context, rule_flags, rule_score)
        except Exception as e:
            self.log_error("fraud_llm_failed", error=str(e))
            return await self._demo_fraud_check(context, rule_flags, rule_score)

    def _run_rule_checks(self, context: ClaimContext) -> tuple[list[str], int]:
        flags = []
        score = 0
        policy = context.policy_data or {}
        submission = context.submission

        # Rule 1: Claim within 30 days of policy start
        policy_start = policy.get("start_date", "2000-01-01")
        incident_date = submission.incident_date or datetime.now().strftime("%Y-%m-%d")
        days_since_start = _days_between(policy_start, incident_date)
        if days_since_start < 30:
            flags.append(f"EARLY_CLAIM: Claim filed {days_since_start} days after policy inception (< 30 days)")
            score += 25

        # Rule 2: Claim amount = exact policy limit (suspicious round number)
        sum_insured = float(policy.get("sum_insured", 1))
        claim_amount = submission.claim_amount
        ratio = claim_amount / sum_insured if sum_insured > 0 else 0
        if 0.98 <= ratio <= 1.0:
            flags.append(f"LIMIT_CLAIM: Claim amount (₹{claim_amount:,.0f}) is {ratio:.1%} of sum insured — suspicious")
            score += 30

        # Rule 3: Very high amount relative to incident type
        if context.claim_type and context.claim_type.value == "Motor":
            if claim_amount > 500000:
                flags.append(f"HIGH_MOTOR_CLAIM: Motor claim of ₹{claim_amount:,.0f} is unusually high")
                score += 15

        # Rule 4: No document confidence issues
        low_confidence_docs = [
            d for d in context.extracted_documents
            if d.get("extraction_confidence", 1.0) < 0.5
        ]
        if low_confidence_docs:
            flags.append(f"LOW_DOC_CONFIDENCE: {len(low_confidence_docs)} document(s) with low extraction confidence — possible tampering")
            score += 20

        # Rule 5: Description extremely short (lack of detail is suspicious for high amounts)
        if len(submission.description) < 50 and claim_amount > 100000:
            flags.append("VAGUE_DESCRIPTION: Very brief description for a high-value claim")
            score += 10

        return flags, min(score, 100)

    async def _demo_fraud_check(
        self, context: ClaimContext, rule_flags: list[str], rule_score: int
    ) -> ClaimContext:
        await asyncio.sleep(0.3)

        if rule_score >= 60:
            risk_level = "HIGH"
        elif rule_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        if not rule_flags:
            reasoning = "No fraud indicators detected. Claim pattern is consistent with legitimate submissions."
        else:
            reasoning = f"Fraud indicators found: {'; '.join(rule_flags)}. Manual review recommended."

        context.fraud_result = FraudResult(
            fraud_score=rule_score,
            risk_level=risk_level,
            flags=rule_flags,
            reasoning=reasoning,
        )
        context.add_audit(
            agent_name=self.name,
            action="FRAUD_CHECK_COMPLETE",
            details={
                "fraud_score": rule_score,
                "risk_level": risk_level,
                "flags": rule_flags,
                "rule_based": True,
            },
        )
        return context

    async def _llm_fraud_check(
        self, context: ClaimContext, rule_flags: list[str], rule_score: int
    ) -> ClaimContext:
        policy = context.policy_data or {}
        submission = context.submission
        policy_start = policy.get("start_date", "2000-01-01")
        sum_insured = float(policy.get("sum_insured", 1))
        ratio = submission.claim_amount / sum_insured

        doc_summary = {
            d.get("doc_type"): d.get("normalized_fields", {})
            for d in context.extracted_documents
        }

        user_msg = FRAUD_USER_TEMPLATE.format(
            claim_id=context.claim_id,
            policy_id=submission.policy_id,
            claim_type=context.claim_type.value if context.claim_type else "Unknown",
            claim_amount=submission.claim_amount,
            sum_insured=sum_insured,
            ratio=ratio,
            policy_start=policy_start,
            incident_date=submission.incident_date,
            days_since_start=_days_between(policy_start, submission.incident_date),
            description=submission.description,
            channel=submission.channel.value,
            document_summary=json.dumps(doc_summary, indent=2)[:2000],
            claim_history="No prior claims found in system.",
        )

        raw = await self.call_llm(
            messages=[
                {"role": "system", "content": FRAUD_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )
        result = json.loads(raw)

        llm_score = int(result.get("fraud_score", 0))
        all_flags = rule_flags + [f for f in result.get("flags", []) if f not in rule_flags]
        final_score = min(max(rule_score, llm_score), 100)

        if final_score >= 60:
            risk_level = "HIGH"
        elif final_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        context.fraud_result = FraudResult(
            fraud_score=final_score,
            risk_level=risk_level,
            flags=all_flags,
            reasoning=result.get("reasoning", ""),
        )
        context.add_audit(
            agent_name=self.name,
            action="FRAUD_CHECK_COMPLETE",
            details={
                "fraud_score": final_score,
                "risk_level": risk_level,
                "flags": all_flags,
                "llm_score": llm_score,
                "rule_score": rule_score,
            },
        )
        return context
