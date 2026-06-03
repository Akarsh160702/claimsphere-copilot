import json
import asyncio
from backend.agents.base_agent import BaseAgent
from backend.models.claim import ClaimContext, ClaimType, MissingInfoResult, ClaimStatus

REQUIRED_FIELDS = {
    ClaimType.HEALTH: {
        "documents": ["hospital_bill", "id_proof"],
        "claim_fields": ["incident_date", "description", "policy_id"],
        "document_fields": {
            "hospital_bill": ["hospital_name", "total_amount", "admission_date"],
            "discharge_summary": ["diagnosis", "discharge_date"],
        },
    },
    ClaimType.MOTOR: {
        "documents": ["fir", "repair_estimate", "id_proof"],
        "claim_fields": ["incident_date", "description", "policy_id"],
        "document_fields": {
            "fir": ["fir_number", "incident_description", "vehicle_number"],
            "repair_estimate": ["total_estimate", "garage_name"],
        },
    },
    ClaimType.PROPERTY: {
        "documents": ["damage_photos", "repair_estimate", "id_proof"],
        "claim_fields": ["incident_date", "description", "policy_id"],
        "document_fields": {
            "repair_estimate": ["total_estimate"],
            "damage_photos": [],
        },
    },
    ClaimType.TRAVEL: {
        "documents": ["id_proof"],
        "claim_fields": ["incident_date", "description", "policy_id"],
        "document_fields": {},
    },
}

FOLLOW_UP_TEMPLATES = {
    ClaimType.HEALTH: """Dear {name},

We have received your health insurance claim (ID: {claim_id}) for ₹{amount:,.0f}.

To process your claim, we require the following additional documents/information:
{missing_list}

Please submit these within 7 working days to avoid delay in processing.
You can upload documents at: {upload_url}

For assistance, contact our Claims Helpline: 1800-XXX-XXXX (24x7)

Regards,
ClaimSphere Claims Team""",

    ClaimType.MOTOR: """Dear {name},

We have received your motor insurance claim (ID: {claim_id}) for ₹{amount:,.0f}.

To expedite your claim, please provide:
{missing_list}

Please note: Delay in document submission may impact your settlement timeline.
Upload portal: {upload_url}

Regards,
ClaimSphere Claims Team""",

    ClaimType.PROPERTY: """Dear {name},

Your property insurance claim (ID: {claim_id}) has been registered.

We need the following to proceed:
{missing_list}

A surveyor will also be assigned for physical inspection within 48 hours.
Upload portal: {upload_url}

Regards,
ClaimSphere Claims Team""",
}


class MissingInfoAgent(BaseAgent):
    def __init__(self):
        super().__init__("MissingInfoAgent")

    async def process(self, context: ClaimContext) -> ClaimContext:
        self.log("checking_missing_info", claim_id=context.claim_id)

        if self.settings.demo_mode:
            return await self._demo_check(context)

        try:
            return await self._llm_check(context)
        except Exception as e:
            self.log_error("missing_info_check_failed", error=str(e))
            return await self._demo_check(context)

    async def _demo_check(self, context: ClaimContext) -> ClaimContext:
        await asyncio.sleep(0.2)
        missing = []
        claim_type = context.claim_type or ClaimType.HEALTH
        requirements = REQUIRED_FIELDS.get(claim_type, {})
        submitted_doc_types = {
            d.get("doc_type", "unknown") for d in context.extracted_documents
        }

        # Check required documents
        for req_doc in requirements.get("documents", []):
            if not any(req_doc in dt for dt in submitted_doc_types):
                missing.append(f"Document: {req_doc.replace('_', ' ').title()}")

        # Check if key extraction fields are present
        for doc in context.extracted_documents:
            doc_type = doc.get("doc_type", "")
            required_doc_fields = requirements.get("document_fields", {}).get(doc_type, [])
            normalized = doc.get("normalized_fields", {})
            for field in required_doc_fields:
                if not normalized.get(field):
                    missing.append(f"Field missing in {doc_type}: {field.replace('_', ' ')}")

        has_missing = len(missing) > 0
        follow_up_msg = ""

        if has_missing:
            template = FOLLOW_UP_TEMPLATES.get(
                claim_type, FOLLOW_UP_TEMPLATES[ClaimType.HEALTH]
            )
            missing_list = "\n".join(f"  • {m}" for m in missing)
            follow_up_msg = template.format(
                name=context.submission.claimant.name,
                claim_id=context.claim_id,
                amount=context.submission.claim_amount,
                missing_list=missing_list,
                upload_url=f"https://claimsphere.demo/upload/{context.claim_id}",
            )
            context.status = ClaimStatus.PENDING_INFO

        context.missing_info_result = MissingInfoResult(
            has_missing_info=has_missing,
            missing_fields=missing,
            follow_up_message=follow_up_msg,
            follow_up_channel="email",
        )
        context.add_audit(
            agent_name=self.name,
            action="MISSING_INFO_CHECK",
            details={
                "has_missing": has_missing,
                "missing_count": len(missing),
                "missing_fields": missing,
            },
        )
        return context

    async def _llm_check(self, context: ClaimContext) -> ClaimContext:
        await asyncio.sleep(0.3)

        system_prompt = """You are an insurance claims specialist identifying missing information.
Analyze the claim and determine what required documents or data fields are missing.
Return JSON only."""

        user_msg = f"""Claim Type: {context.claim_type.value if context.claim_type else 'Health'}
Submitted Documents: {[d.get('doc_type') for d in context.extracted_documents]}
Extracted Fields: {json.dumps({d.get('doc_type'): list(d.get('normalized_fields', {}).keys()) for d in context.extracted_documents})}
Claim Amount: {context.submission.claim_amount}
Description: {context.submission.description}

Identify missing required documents and fields. Return:
{{
    "has_missing_info": true/false,
    "missing_fields": ["list of missing items"],
    "follow_up_message": "polite email to customer requesting items",
    "priority_missing": ["most critical missing items"]
}}"""

        raw = await self.call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )
        result = json.loads(raw)

        has_missing = result.get("has_missing_info", False)
        if has_missing:
            context.status = ClaimStatus.PENDING_INFO

        context.missing_info_result = MissingInfoResult(
            has_missing_info=has_missing,
            missing_fields=result.get("missing_fields", []),
            follow_up_message=result.get("follow_up_message", ""),
            follow_up_channel="email",
        )
        context.add_audit(
            agent_name=self.name,
            action="MISSING_INFO_CHECK",
            details={"has_missing": has_missing, "missing": result.get("missing_fields", [])},
        )
        return context
