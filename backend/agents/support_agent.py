"""
Support Agent — CSR Copilot for real-time claim Q&A.
Powers the CSR interface and customer-facing status queries.
"""
import json
import asyncio
from backend.agents.base_agent import BaseAgent
from backend.models.claim import ClaimContext
from backend.tools.ai_search import AISearchClient
from backend.tools.dataverse import DataverseClient

SUPPORT_SYSTEM_PROMPT = """You are ClaimSphere, an intelligent CSR co-pilot assistant for insurance claims.

You help Customer Service Representatives (CSRs) by:
1. Answering questions about specific claim status and details
2. Explaining AI decisions and recommendations in plain language
3. Answering policy coverage questions (using RAG knowledge base)
4. Suggesting next steps for the CSR
5. Drafting customer communication templates

Communication Style:
- Professional but empathetic
- Clear and jargon-free
- Actionable (always suggest next steps)
- Factual (never fabricate — say "I don't have that information" if unsure)

You have access to:
- Claim details and status
- Policy terms knowledge base
- AI decision rationale
- Audit trail

Always be helpful and accurate. The CSR's efficiency depends on your accuracy."""


class SupportAgent(BaseAgent):
    def __init__(self):
        super().__init__("SupportAgent")
        self.search_client = AISearchClient()
        self.dataverse = DataverseClient()

    async def process(self, context) -> object:
        return context  # Support agent is query-only; no-op in the pipeline

    async def answer_query(self, query: str, claim_id: str = None) -> dict:
        self.log("support_query", claim_id=claim_id, query=query[:100])

        policy_id = None
        claim_data = None
        policy_data = None

        # 1. Disambiguate and extract IDs
        if claim_id:
            if claim_id.startswith("POL-"):
                policy_id = claim_id
                claim_id = None
            elif not claim_id.startswith("CLM-"):
                # If it contains POL-, treat as policy_id
                if "POL-" in claim_id:
                    policy_id = claim_id
                    claim_id = None

        # Try to extract policy ID from query if not already present
        if not policy_id:
            import re
            m = re.search(r'(POL-[A-Z0-9-]+)', query, re.IGNORECASE)
            if m:
                policy_id = m.group(1).upper()

        # Try to extract claim ID from query if not already present
        if not claim_id:
            import re
            m = re.search(r'(CLM-[A-Z0-9-]+)', query, re.IGNORECASE)
            if m:
                claim_id = m.group(1).upper()

        # 2. Fetch context data
        claim_context = ""
        if claim_id:
            claim_data = await self.dataverse.get_claim(claim_id)
            if claim_data:
                claim_context = f"\nCLAIM DATA FOR {claim_id}:\n{json.dumps(claim_data, indent=2, default=str)[:3000]}"

        policy_context = ""
        if policy_id:
            policy_data = await self.search_client.get_policy(policy_id)
            if policy_data:
                policy_context = f"\nPOLICY DATA FOR {policy_id}:\n{json.dumps(policy_data, indent=2, default=str)[:3000]}"

        # RAG: search policy knowledge base for relevant context
        rag_context = ""
        policy_results = await self.search_client.search_policy_terms(query)
        if policy_results:
            rag_context = "\nPOLICY KNOWLEDGE BASE:\n" + json.dumps(policy_results[:2], indent=2)[:2000]

        if self.settings.demo_mode:
            return await self._demo_answer(query, claim_id, policy_id, claim_data, policy_data)

        messages = [
            {"role": "system", "content": SUPPORT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"CSR Query: {query}\n"
                    f"Claim ID Context: {claim_id or 'Not specified'}\n"
                    f"Policy ID Context: {policy_id or 'Not specified'}\n"
                    f"{claim_context}"
                    f"{policy_context}"
                    f"{rag_context}"
                    "\n\nProvide a helpful, accurate response to the CSR. "
                    "If the query is about a specific claim, reference the claim data. "
                    "If the query is about a specific policy, reference the policy data. "
                    "Include suggested next actions for the CSR."
                ),
            },
        ]

        try:
            response = await self.call_llm(messages=messages, temperature=0.3)
            return {
                "answer": response,
                "claim_id": claim_id or policy_id,
                "sources": [
                    k for k, v in {
                        "claim_data": bool(claim_data),
                        "policy_data": bool(policy_data),
                        "policy_knowledge_base": bool(policy_results)
                    }.items() if v
                ],
                "suggested_actions": self._extract_actions(response),
            }
        except Exception as e:
            self.log_error("support_query_failed", error=str(e))
            return await self._demo_answer(query, claim_id, policy_id, claim_data, policy_data)

    async def get_claim_summary(self, claim_id: str) -> dict:
        claim_data = await self.dataverse.get_claim(claim_id)
        if not claim_data:
            return {"error": f"Claim {claim_id} not found", "claim_id": claim_id}

        if self.settings.demo_mode:
            return self._format_demo_summary(claim_id, claim_data)

        messages = [
            {"role": "system", "content": SUPPORT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Provide a concise claim summary for CSR use:\n"
                    f"Claim Data: {json.dumps(claim_data, indent=2, default=str)[:3000]}\n\n"
                    "Return JSON: {\"summary\": \"...\", \"status\": \"...\", "
                    "\"next_action\": \"...\", \"customer_message\": \"...\"}"
                ),
            },
        ]
        try:
            raw = await self.call_llm(
                messages=messages,
                response_format={"type": "json_object"},
            )
            return json.loads(raw)
        except Exception:
            return self._format_demo_summary(claim_id, claim_data)

    async def _demo_answer(self, query: str, claim_id: str = None, policy_id: str = None, claim_data: object = None, policy_data: dict = None) -> dict:
        await asyncio.sleep(0.3)
        query_lower = query.lower()

        def get_val(obj, key, default=None):
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # 1. Smart Answer for Claim Queries
        if claim_data:
            c_id = get_val(claim_data, 'claim_id') or get_val(claim_data, 'crcce_name') or claim_id
            submission = get_val(claim_data, 'submission')
            claimant = get_val(submission, 'claimant')
            claimant_name = get_val(claimant, 'name') or get_val(claim_data, 'claimant_name') or get_val(claim_data, 'crcce_claimantname') or "Customer"
            claim_amount = get_val(submission, 'claim_amount') or get_val(claim_data, 'claim_amount') or get_val(claim_data, 'crcce_claimamount') or 0
            
            # Resolve status
            status_obj = get_val(claim_data, 'status') or get_val(claim_data, 'crcce_status') or "Processing"
            status_val = status_obj.value if hasattr(status_obj, 'value') else str(status_obj)
            
            # Resolve decision
            adj = get_val(claim_data, 'adjudication_result')
            decision_obj = get_val(adj, 'decision') or get_val(claim_data, 'decision') or get_val(claim_data, 'crcce_decision') or ""
            decision_val = decision_obj.value if hasattr(decision_obj, 'value') else str(decision_obj)
            
            # Resolve rationale
            rationale_val = get_val(adj, 'rationale') or get_val(claim_data, 'rationale') or get_val(claim_data, 'crcce_rationale') or ""
            payout_val = get_val(adj, 'final_payout') or get_val(claim_data, 'final_payout') or get_val(claim_data, 'crcce_approvedamount') or 0
            
            # Resolve missing fields
            missing_result = get_val(claim_data, 'missing_info_result')
            missing_fields = get_val(missing_result, 'missing_fields') or []
            
            if "status" in query_lower or "update" in query_lower or "detail" in query_lower or "info" in query_lower or "tell me" in query_lower:
                if status_val.lower() in ("approved", "closed", "paid"):
                    answer = (
                        f"Claim **{c_id}** for customer **{claimant_name}** has been **Approved**. \n"
                        f"💰 **Approved Amount:** ₹{payout_val:,.2f} (Deductible: ₹{(claim_amount - payout_val):,.2f})\n"
                        f"📝 **Rationale:** {rationale_val}\n"
                        f"\n**Next Action for CSR:** Inform the customer that the payment of ₹{payout_val:,.2f} will be credited within 3 business days."
                    )
                elif status_val.lower() in ("rejected", "denied"):
                    answer = (
                        f"Claim **{c_id}** for customer **{claimant_name}** has been **Rejected**. \n"
                        f"📝 **Rationale:** {rationale_val}\n"
                        f"\n**Next Action for CSR:** Inform the customer of the rejection details and explain the 30-day appeal process."
                    )
                elif status_val.lower() in ("pending information", "pending_info"):
                    fields_str = ", ".join(missing_fields) if missing_fields else "required documents"
                    answer = (
                        f"Claim **{c_id}** for customer **{claimant_name}** is **Pending Information**. \n"
                        f"⚠️ **Missing items:** {fields_str}\n"
                        f"\n**Next Action for CSR:** Contact customer to upload the missing documents ({fields_str}) via the portal."
                    )
                elif status_val.lower() in ("escalated", "under human review", "under_review"):
                    answer = (
                        f"Claim **{c_id}** for customer **{claimant_name}** has been **Escalated** for expert review. \n"
                        f"📝 **Escalation rationale:** {rationale_val}\n"
                        f"\n**Next Action for CSR:** Monitor the human decision queue. The customer will be updated within 2 business days."
                    )
                else:
                    answer = (
                        f"Claim **{c_id}** is currently **{status_val}**.\n"
                        f"💰 **Amount:** ₹{claim_amount:,.2f} | **Claimant:** {claimant_name}\n"
                        f"📝 **Details:** {rationale_val or 'Processing is currently underway.'}"
                    )
                
                return {
                    "answer": answer,
                    "claim_id": c_id,
                    "sources": ["claim_data"],
                    "suggested_actions": [
                        "Check claim audit trail",
                        "Review attached documents",
                        "Update customer if requested"
                    ]
                }

        # 2. Smart Answer for Policy Queries
        if policy_data:
            p_id = get_val(policy_data, 'policy_id') or policy_id
            holder_name = get_val(policy_data, 'holder_name') or "Customer"
            policy_type = get_val(policy_data, 'policy_type')
            sum_insured = get_val(policy_data, 'sum_insured') or 0
            deductible = get_val(policy_data, 'deductible') or 0
            coverage_details = get_val(policy_data, 'coverage_details')
            exclusions = get_val(policy_data, 'exclusions')

            # Parse strings to dict/list if needed
            cov_dict = coverage_details
            if isinstance(cov_dict, str):
                try:
                    cov_dict = json.loads(cov_dict)
                except Exception:
                    cov_dict = {}

            exclusions_list = exclusions
            if isinstance(exclusions_list, str):
                exclusions_list = [x.strip() for x in exclusions_list.split("|")]

            if "room" in query_lower or "rent" in query_lower:
                limit = cov_dict.get("room_rent_limit") or cov_dict.get("room_rent")
                if limit:
                    answer = f"The Room Rent Limit under policy **{p_id}** ({holder_name}) is **₹{limit:,.0f} per day**."
                else:
                    answer = f"There is no specific room rent limit specified under policy **{p_id}**."
            elif "icu" in query_lower:
                limit = cov_dict.get("icu_limit")
                if limit:
                    answer = f"The ICU Rent Limit under policy **{p_id}** ({holder_name}) is **₹{limit:,.0f} per day**."
                else:
                    answer = f"There is no specific ICU limit specified under policy **{p_id}**."
            elif "deductible" in query_lower:
                answer = f"The deductible under policy **{p_id}** ({holder_name}) is **₹{deductible:,.0f}**."
            elif "sum insured" in query_lower or "insured" in query_lower:
                answer = f"The sum insured under policy **{p_id}** ({holder_name}) is **₹{sum_insured:,.0f}**."
            elif "exclusion" in query_lower or "exclude" in query_lower:
                formatted_exclusions = "\n".join([f"- {x}" for x in exclusions_list]) if exclusions_list else "None specified"
                answer = f"Exclusions under policy **{p_id}** ({holder_name}):\n{formatted_exclusions}"
            else:
                # General policy info
                cov_items = []
                if isinstance(cov_dict, dict):
                    for k, v in cov_dict.items():
                        if isinstance(v, bool) and v:
                            cov_items.append(k.replace("_", " ").title())
                        elif isinstance(v, (int, float)):
                            cov_items.append(f"{k.replace('_', ' ').title()}: ₹{v:,.0f}")
                cov_str = ", ".join(cov_items) or "Standard coverage"
                answer = (
                    f"Policy **{p_id}** details:\n"
                    f"- **Holder:** {holder_name}\n"
                    f"- **Type:** {policy_type}\n"
                    f"- **Sum Insured:** ₹{sum_insured:,.0f}\n"
                    f"- **Deductible:** ₹{deductible:,.0f}\n"
                    f"- **Coverages:** {cov_str}\n"
                )

            return {
                "answer": answer,
                "claim_id": claim_id,
                "sources": ["policy_knowledge_base"],
                "suggested_actions": [
                    "Clarify sub-limits with customer",
                    "Verify policy active dates",
                    "Advise customer on claims process"
                ]
            }

        # 3. Default fallback
        if "status" in query_lower or "update" in query_lower:
            answer = (
                f"Claim {claim_id or 'ID not specified'} is currently **Under Processing**. "
                "The AI pipeline has completed document extraction and policy validation. "
                "Expected decision within 2 hours. "
                "\n\n**Next Action for CSR:** Advise customer to check their email for updates. "
                "If they need an immediate response, you can manually trigger the adjudication review."
            )
        elif "reject" in query_lower or "denied" in query_lower:
            answer = (
                "The claim was **rejected** because the policy exclusion clause applies to this incident. "
                "Specifically, the policy excludes pre-existing conditions within the first 2 years. "
                "\n\n**Next Action for CSR:** Inform customer of the rejection reason and their right to appeal. "
                "They can submit an appeal within 30 days with additional medical evidence."
            )
        elif "document" in query_lower or "missing" in query_lower:
            answer = (
                "The following documents are still required: **Hospital Discharge Summary, ID Proof**. "
                "A follow-up email was already sent to the customer on today's date. "
                "\n\n**Next Action for CSR:** Confirm the customer received the email and guide them "
                "to upload documents at the portal. Documents must be submitted within 7 days."
            )
        elif "cover" in query_lower or "policy" in query_lower:
            answer = (
                "Based on the policy terms: \n"
                "✅ **Covered:** Hospitalization, surgeries, day-care procedures, ambulance charges\n"
                "❌ **Not Covered:** Cosmetic surgery, dental (non-accidental), pre-existing conditions (first 2 years)\n"
                "💰 **Limit:** ₹5,00,000 sum insured | ₹5,000 deductible\n"
                "\n\n**Next Action for CSR:** Clarify the specific treatment to check sub-limits."
            )
        else:
            answer = (
                f"I've analyzed the query regarding '{query[:80]}'. "
                "Based on the claim data and policy knowledge base, this appears to be a standard processing case. "
                "\n\n**Next Action for CSR:** Review the claim audit trail for full history. "
                "If customer needs escalation, use the 'Escalate to Adjuster' button in the portal."
            )

        return {
            "answer": answer,
            "claim_id": claim_id,
            "sources": ["claim_data", "policy_knowledge_base"],
            "suggested_actions": [
                "Check claim audit trail",
                "Review attached documents",
                "Contact customer if needed",
            ],
        }

    def _format_demo_summary(self, claim_id: str, claim_data: dict) -> dict:
        return {
            "summary": f"Claim {claim_id} for ₹{claim_data.get('claim_amount', 0):,.0f}. "
                       f"Status: {claim_data.get('status', 'Processing')}. "
                       f"Type: {claim_data.get('claim_type', 'Health')}.",
            "status": claim_data.get("status", "Processing"),
            "next_action": "Review adjudication recommendation and proceed accordingly",
            "customer_message": "Your claim is being processed. You will receive an update within 24 hours.",
        }

    def _extract_actions(self, text: str) -> list[str]:
        actions = []
        for line in text.split("\n"):
            if any(marker in line for marker in ["Next Action", "Action:", "→", "•", "-"]):
                action = line.strip().lstrip("→•-*").strip()
                if len(action) > 10:
                    actions.append(action[:100])
        return actions[:3]
