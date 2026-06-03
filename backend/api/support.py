from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.agents.support_agent import SupportAgent

router = APIRouter(prefix="/support", tags=["CSR Support"])


class SupportQuery(BaseModel):
    query: str
    claim_id: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/query", response_model=dict)
async def answer_query(body: SupportQuery):
    """Answer a CSR query about a claim or policy."""
    agent = SupportAgent()
    return await agent.answer_query(query=body.query, claim_id=body.claim_id)


@router.get("/claim/{claim_id}/summary", response_model=dict)
async def get_claim_summary(claim_id: str):
    """Get a CSR-friendly summary of a claim."""
    agent = SupportAgent()
    return await agent.get_claim_summary(claim_id)
