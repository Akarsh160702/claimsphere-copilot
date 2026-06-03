import json
import asyncio
from backend.agents.base_agent import BaseAgent
from backend.models.claim import ClaimContext, ClaimType, ClaimPriority, ClaimStatus

ROUTER_SYSTEM_PROMPT = """You are an expert insurance claims classifier at a leading insurance company.

Your job is to analyze submitted claim information and:
1. Identify the claim type (Health, Motor, Property, Travel)
2. Assess claim priority based on amount and urgency
3. List the required documents for this claim type
4. Note any initial observations

Claim Priority Rules:
- HIGH: Amount > ₹1,00,000 OR potential life-threatening medical situation
- MEDIUM: Amount ₹25,000 - ₹1,00,000
- LOW: Amount < ₹25,000

Required Documents by Claim Type:
Health: policy_id, hospital_bill, discharge_summary, id_proof, prescription (if medicines)
Motor: policy_id, fir_copy, repair_estimate, vehicle_photos, id_proof, driving_license
Property: policy_id, damage_photos, repair_estimate, id_proof, ownership_proof, surveyor_report
Travel: policy_id, passport, travel_tickets, medical_report (if medical), id_proof

Always respond with valid JSON only. No markdown, no explanation outside JSON."""

ROUTER_USER_TEMPLATE = """Analyze this insurance claim submission:

Policy ID: {policy_id}
Claimed Amount: ₹{claim_amount}
Incident Date: {incident_date}
Description: {description}
Already Submitted Documents: {submitted_docs}
Submission Channel: {channel}

Return JSON with this exact structure:
{{
    "claim_type": "Health|Motor|Property|Travel",
    "priority": "HIGH|MEDIUM|LOW",
    "required_documents": ["doc1", "doc2"],
    "submitted_documents": ["doc1"],
    "missing_documents": ["doc2"],
    "initial_observations": "brief notes about the claim",
    "auto_classification_confidence": 0.95,
    "urgency_flag": false
}}"""


class RouterAgent(BaseAgent):
    def __init__(self):
        super().__init__("RouterAgent")

    async def process(self, context: ClaimContext) -> ClaimContext:
        self.log("routing_claim", claim_id=context.claim_id)
        context.status = ClaimStatus.PROCESSING

        if self.settings.demo_mode:
            return await self._demo_route(context)

        try:
            submission = context.submission
            user_msg = ROUTER_USER_TEMPLATE.format(
                policy_id=submission.policy_id,
                claim_amount=submission.claim_amount,
                incident_date=submission.incident_date,
                description=submission.description,
                submitted_docs=", ".join(submission.document_urls) or "None",
                channel=submission.channel.value,
            )
            raw = await self.call_llm(
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
            )
            result = json.loads(raw)
            context.claim_type = ClaimType(result.get("claim_type", "Health"))
            context.priority = ClaimPriority(result.get("priority", "MEDIUM"))
            context.add_audit(
                agent_name=self.name,
                action="CLAIM_CLASSIFIED",
                details={
                    "claim_type": context.claim_type.value,
                    "priority": context.priority.value,
                    "confidence": result.get("auto_classification_confidence", 0.9),
                    "required_documents": result.get("required_documents", []),
                    "missing_documents": result.get("missing_documents", []),
                    "initial_observations": result.get("initial_observations", ""),
                },
            )
            self.log("claim_routed", claim_id=context.claim_id, type=context.claim_type.value)
        except Exception as e:
            self.log_error("routing_failed", error=str(e), claim_id=context.claim_id)
            context = await self._demo_route(context)

        return context

    async def _demo_route(self, context: ClaimContext) -> ClaimContext:
        await asyncio.sleep(0.3)
        description = context.submission.description.lower()
        amount = context.submission.claim_amount

        if any(w in description for w in ["hospital", "surgery", "medical", "health", "treatment", "diagnosis"]):
            context.claim_type = ClaimType.HEALTH
        elif any(w in description for w in ["car", "vehicle", "accident", "motor", "fir", "repair"]):
            context.claim_type = ClaimType.MOTOR
        elif any(w in description for w in ["property", "house", "damage", "flood", "fire", "building"]):
            context.claim_type = ClaimType.PROPERTY
        elif any(w in description for w in ["travel", "flight", "trip", "passport"]):
            context.claim_type = ClaimType.TRAVEL
        else:
            context.claim_type = context.submission.claim_type or ClaimType.HEALTH

        if amount > 100000:
            context.priority = ClaimPriority.HIGH
        elif amount > 25000:
            context.priority = ClaimPriority.MEDIUM
        else:
            context.priority = ClaimPriority.LOW

        required_docs = {
            ClaimType.HEALTH: ["hospital_bill", "discharge_summary", "id_proof"],
            ClaimType.MOTOR: ["fir_copy", "repair_estimate", "vehicle_photos", "id_proof"],
            ClaimType.PROPERTY: ["damage_photos", "repair_estimate", "id_proof", "ownership_proof"],
            ClaimType.TRAVEL: ["passport", "travel_tickets", "id_proof"],
        }

        context.add_audit(
            agent_name=self.name,
            action="CLAIM_CLASSIFIED",
            details={
                "claim_type": context.claim_type.value,
                "priority": context.priority.value,
                "confidence": 0.92,
                "required_documents": required_docs.get(context.claim_type, []),
                "initial_observations": f"Claim classified as {context.claim_type.value} with {context.priority.value} priority based on description and amount.",
            },
        )
        return context
