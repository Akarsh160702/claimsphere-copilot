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

        claim_context = ""
        if claim_id:
            claim_data = await self.dataverse.get_claim(claim_id)
            if claim_data:
                claim_context = f"\nCLAIM DATA:\n{json.dumps(claim_data, indent=2, default=str)[:3000]}"

        # RAG: search policy knowledge base for relevant context
        rag_context = ""
        policy_results = await self.search_client.search_policy_terms(query)
        if policy_results:
            rag_context = "\nPOLICY KNOWLEDGE BASE:\n" + json.dumps(policy_results[:2], indent=2)[:2000]

        if self.settings.demo_mode:
            return await self._demo_answer(query, claim_id, claim_context)

        messages = [
            {"role": "system", "content": SUPPORT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"CSR Query: {query}\n"
                    f"Claim ID Context: {claim_id or 'Not specified'}"
                    f"{claim_context}"
                    f"{rag_context}"
                    "\n\nProvide a helpful, accurate response to the CSR. "
                    "If the query is about a specific claim, reference the claim data. "
                    "Include suggested next actions for the CSR."
                ),
            },
        ]

        try:
            response = await self.call_llm(messages=messages, temperature=0.3)
            return {
                "answer": response,
                "claim_id": claim_id,
                "sources": ["claim_data", "policy_knowledge_base"] if claim_context and rag_context else [],
                "suggested_actions": self._extract_actions(response),
            }
        except Exception as e:
            self.log_error("support_query_failed", error=str(e))
            return await self._demo_answer(query, claim_id, claim_context)

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

    async def _demo_answer(self, query: str, claim_id: str, claim_context: str) -> dict:
        await asyncio.sleep(0.3)
        query_lower = query.lower()

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
