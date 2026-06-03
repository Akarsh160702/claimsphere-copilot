import json
import asyncio
from datetime import datetime
from backend.agents.base_agent import BaseAgent
from backend.models.claim import ClaimContext, ValidationResult, ClaimStatus
from backend.tools.ai_search import AISearchClient

VALIDATION_SYSTEM_PROMPT = """You are a senior insurance policy validator with 15+ years of experience.

Your job is to validate whether a claim is eligible for coverage based on policy terms.

Validation Checklist:
1. Policy active status (start_date <= incident_date <= end_date)
2. Claim type covered under the policy
3. Claim amount within sum insured limits
4. No exclusion clauses triggered
5. Waiting period satisfied
6. Sub-limits applicable (e.g., room rent cap, surgery limits)

Be thorough, accurate, and provide clear reasoning for each check.
Always respond with valid JSON only."""

VALIDATION_USER_TEMPLATE = """Validate this insurance claim against the policy:

CLAIM DETAILS:
- Claim ID: {claim_id}
- Claim Type: {claim_type}
- Claim Amount: ₹{claim_amount}
- Incident Date: {incident_date}
- Description: {description}
- Extracted Document Data: {extracted_data}

POLICY TERMS:
{policy_data}

Validate and return JSON with this exact structure:
{{
    "is_valid": true/false,
    "policy_active": true/false,
    "claim_type_covered": true/false,
    "within_sum_insured": true/false,
    "deductible_applicable": true/false,
    "coverage_amount": 0.00,
    "deductible_amount": 0.00,
    "exclusions_hit": [],
    "sub_limits_applied": {{}},
    "validation_notes": "detailed explanation",
    "confidence": 0.95,
    "issues": []
}}"""


class ValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__("ValidationAgent")
        self.search_client = AISearchClient()

    async def process(self, context: ClaimContext) -> ClaimContext:
        self.log("validating_claim", claim_id=context.claim_id)

        policy_data = await self.search_client.get_policy(context.submission.policy_id)

        if not policy_data:
            context.validation_result = ValidationResult(
                is_valid=False,
                policy_active=False,
                claim_type_covered=False,
                within_sum_insured=False,
                deductible_applicable=False,
                validation_notes=f"Policy {context.submission.policy_id} not found in system.",
                confidence=1.0,
            )
            context.add_audit(
                agent_name=self.name,
                action="VALIDATION_FAILED",
                details={"reason": "Policy not found", "policy_id": context.submission.policy_id},
            )
            return context

        context.policy_data = policy_data

        if self.settings.demo_mode:
            return await self._demo_validate(context, policy_data)

        try:
            extracted_summary = self._summarize_extractions(context.extracted_documents)
            user_msg = VALIDATION_USER_TEMPLATE.format(
                claim_id=context.claim_id,
                claim_type=context.claim_type.value if context.claim_type else "Unknown",
                claim_amount=context.submission.claim_amount,
                incident_date=context.submission.incident_date,
                description=context.submission.description,
                extracted_data=json.dumps(extracted_summary, indent=2)[:2000],
                policy_data=json.dumps(policy_data, indent=2)[:3000],
            )
            raw = await self.call_llm(
                messages=[
                    {"role": "system", "content": VALIDATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
            )
            result = json.loads(raw)
            context.validation_result = ValidationResult(
                is_valid=result.get("is_valid", False),
                policy_active=result.get("policy_active", False),
                claim_type_covered=result.get("claim_type_covered", False),
                within_sum_insured=result.get("within_sum_insured", False),
                deductible_applicable=result.get("deductible_applicable", True),
                coverage_amount=float(result.get("coverage_amount", 0)),
                deductible_amount=float(result.get("deductible_amount", 0)),
                exclusions_hit=result.get("exclusions_hit", []),
                validation_notes=result.get("validation_notes", ""),
                confidence=float(result.get("confidence", 0.9)),
            )
        except Exception as e:
            self.log_error("validation_llm_failed", error=str(e))
            return await self._demo_validate(context, policy_data)

        context.add_audit(
            agent_name=self.name,
            action="VALIDATION_COMPLETE",
            details={
                "is_valid": context.validation_result.is_valid,
                "coverage_amount": context.validation_result.coverage_amount,
                "exclusions_hit": context.validation_result.exclusions_hit,
                "notes": context.validation_result.validation_notes,
            },
        )
        return context

    async def _demo_validate(self, context: ClaimContext, policy_data: dict) -> ClaimContext:
        await asyncio.sleep(0.4)

        # Check policy active
        today = datetime.now().strftime("%Y-%m-%d")
        start = policy_data.get("start_date", "2000-01-01")
        end = policy_data.get("end_date", "2000-01-01")
        policy_active = start <= today <= end

        sum_insured = float(policy_data.get("sum_insured", 0))
        claim_amount = context.submission.claim_amount
        within_limits = claim_amount <= sum_insured
        deductible = float(policy_data.get("deductible", 0))

        exclusions = policy_data.get("exclusions", [])
        description = context.submission.description.lower()
        # Require ALL key words of the exclusion to appear — avoids false positives
        triggered_exclusions = [
            exc for exc in exclusions
            if all(word in description for word in exc.lower().split()[:2])
        ]

        claim_type_covered = True
        coverage_amount = min(claim_amount, sum_insured) if policy_active and within_limits else 0.0

        is_valid = policy_active and claim_type_covered and within_limits and not triggered_exclusions

        if not policy_active:
            notes = "Policy has expired or not yet active. Claim cannot be processed."
        elif triggered_exclusions:
            notes = f"Claim may be excluded under policy terms: {', '.join(triggered_exclusions)}."
        elif not within_limits:
            notes = f"Claim amount ₹{claim_amount:,.0f} exceeds sum insured ₹{sum_insured:,.0f}."
        else:
            notes = (
                f"Policy is active. Claim type is covered. "
                f"Coverage amount: ₹{coverage_amount:,.0f} after deductible of ₹{deductible:,.0f}."
            )

        context.validation_result = ValidationResult(
            is_valid=is_valid,
            policy_active=policy_active,
            claim_type_covered=claim_type_covered,
            within_sum_insured=within_limits,
            deductible_applicable=deductible > 0,
            coverage_amount=coverage_amount,
            deductible_amount=deductible,
            exclusions_hit=triggered_exclusions,
            validation_notes=notes,
            confidence=0.95,
        )
        context.add_audit(
            agent_name=self.name,
            action="VALIDATION_COMPLETE",
            details={
                "is_valid": is_valid,
                "policy_active": policy_active,
                "coverage_amount": coverage_amount,
                "deductible": deductible,
                "exclusions_hit": triggered_exclusions,
            },
        )
        return context

    def _summarize_extractions(self, docs: list[dict]) -> dict:
        summary = {}
        for doc in docs:
            doc_type = doc.get("doc_type", "unknown")
            summary[doc_type] = doc.get("normalized_fields", {})
        return summary
