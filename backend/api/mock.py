"""Mock API endpoints simulating external integrations."""
from fastapi import APIRouter
from backend.tools.mock_integrations import (
    MockPolicySystemClient, MockCRMClient, MockPaymentClient
)

router = APIRouter(prefix="/mock", tags=["Mock Integrations"])
policy_client = MockPolicySystemClient()
crm_client = MockCRMClient()
payment_client = MockPaymentClient()


@router.get("/policies/{policy_id}")
async def get_policy(policy_id: str):
    return await policy_client.verify_policy(policy_id)


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    return await crm_client.get_customer(customer_id)


@router.post("/payments/initiate")
async def initiate_payment(body: dict):
    return await payment_client.initiate_payout(
        claim_id=body.get("claim_id"),
        amount=body.get("amount"),
        beneficiary=body.get("beneficiary"),
    )


@router.get("/policies")
async def list_policies():
    from backend.tools.ai_search import DEMO_POLICIES
    return list(DEMO_POLICIES.values())
