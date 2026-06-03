"""
Mock APIs for CRM, Payment, and Policy systems.
These simulate external integrations not available in the sandbox.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional


class MockPolicySystemClient:
    """Simulates an external policy management system."""

    POLICY_DB = {
        "POL-HEALTH-001": {"status": "active", "holder": "Rahul Sharma", "type": "Health"},
        "POL-MOTOR-001": {"status": "active", "holder": "Priya Nair", "type": "Motor"},
        "POL-PROPERTY-001": {"status": "active", "holder": "Suresh Kumar", "type": "Property"},
        "POL-HEALTH-EXPIRED": {"status": "expired", "holder": "Test User", "type": "Health"},
    }

    async def verify_policy(self, policy_id: str) -> dict:
        await asyncio.sleep(0.1)
        policy = self.POLICY_DB.get(policy_id)
        if not policy:
            return {"found": False, "status": "not_found"}
        return {"found": True, **policy}

    async def get_claim_history(self, holder_id: str) -> list[dict]:
        await asyncio.sleep(0.1)
        return [
            {
                "claim_id": "CLM-2024-PREV-001",
                "date": "2024-02-15",
                "amount": 12000,
                "type": "Health",
                "status": "Settled",
            }
        ]


class MockCRMClient:
    """Simulates a CRM system for customer data."""

    CUSTOMER_DB = {
        "CUST-001": {
            "name": "Rahul Sharma",
            "email": "rahul.sharma@email.com",
            "phone": "+91-9876543210",
            "tier": "Gold",
            "since": "2020-01-15",
        },
        "CUST-002": {
            "name": "Priya Nair",
            "email": "priya.nair@email.com",
            "phone": "+91-9876543211",
            "tier": "Silver",
            "since": "2021-06-20",
        },
        "CUST-003": {
            "name": "Suresh Kumar",
            "email": "suresh.kumar@email.com",
            "phone": "+91-9876543212",
            "tier": "Platinum",
            "since": "2019-03-10",
        },
    }

    async def get_customer(self, customer_id: str) -> Optional[dict]:
        await asyncio.sleep(0.05)
        return self.CUSTOMER_DB.get(customer_id)

    async def update_claim_status(self, customer_id: str, claim_id: str, status: str) -> bool:
        await asyncio.sleep(0.05)
        return True

    async def send_notification(self, customer_id: str, message: str, channel: str = "email") -> bool:
        await asyncio.sleep(0.05)
        print(f"[MOCK CRM] Notification to {customer_id} via {channel}: {message[:100]}")
        return True


class MockPaymentClient:
    """Simulates a payment processing system."""

    async def initiate_payout(
        self, claim_id: str, amount: float, beneficiary: str, bank_details: dict = None
    ) -> dict:
        await asyncio.sleep(0.2)
        txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        return {
            "txn_id": txn_id,
            "claim_id": claim_id,
            "amount": amount,
            "beneficiary": beneficiary,
            "status": "initiated",
            "expected_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "utr_number": f"UTR{uuid.uuid4().hex[:12].upper()}",
        }

    async def get_payout_status(self, txn_id: str) -> dict:
        await asyncio.sleep(0.05)
        return {
            "txn_id": txn_id,
            "status": "processing",
            "message": "Payment processing initiated",
        }


class MockNotificationClient:
    """Simulates email/SMS notification service."""

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        await asyncio.sleep(0.05)
        print(f"[MOCK EMAIL] To: {to} | Subject: {subject}")
        return True

    async def send_sms(self, phone: str, message: str) -> bool:
        await asyncio.sleep(0.05)
        print(f"[MOCK SMS] To: {phone} | Message: {message[:100]}")
        return True

    async def send_teams_card(self, webhook_url: str, card_payload: dict) -> bool:
        await asyncio.sleep(0.1)
        print(f"[MOCK TEAMS] Card sent to webhook | Claim: {card_payload.get('claim_id')}")
        return True
