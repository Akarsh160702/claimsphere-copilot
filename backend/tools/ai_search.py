import json
import asyncio
from typing import Optional
import structlog

from backend.config import get_settings

logger = structlog.get_logger()

DEMO_POLICIES = {
    "POL-HEALTH-001": {
        "policy_id": "POL-HEALTH-001",
        "policy_type": "Health",
        "holder_name": "Rahul Sharma",
        "holder_id": "CUST-001",
        "sum_insured": 2000000.0,
        "premium": 45000.0,
        "deductible": 10000.0,
        "start_date": "2024-01-01",
        "end_date": "2030-12-31",
        "waiting_period_days": 30,
        "coverage_details": {
            "hospitalization": True,
            "day_care": True,
            "pre_hospitalization_days": 30,
            "post_hospitalization_days": 60,
            "room_rent_limit": 5000,
            "icu_limit": 10000,
            "ambulance_cover": 2000,
        },
        "exclusions": [
            "Cosmetic surgery",
            "Self-inflicted injuries",
            "War and terrorism",
            "Pre-existing conditions within first 2 years",
            "Dental treatment (unless accidental)",
            "Vision correction (spectacles/lenses)",
        ],
        "sub_limits": {
            "cataract": 40000,
            "knee_replacement": 100000,
            "maternity": 50000,
        },
    },
    "POL-MOTOR-001": {
        "policy_id": "POL-MOTOR-001",
        "policy_type": "Motor",
        "holder_name": "Priya Nair",
        "holder_id": "CUST-002",
        "vehicle_number": "TN09AB1234",
        "vehicle_make": "Honda City",
        "vehicle_year": 2020,
        "sum_insured": 850000.0,
        "premium": 22000.0,
        "deductible": 2000.0,
        "start_date": "2024-03-01",
        "end_date": "2030-02-28",
        "waiting_period_days": 0,
        "coverage_details": {
            "own_damage": True,
            "third_party_liability": True,
            "personal_accident": True,
            "theft": True,
            "fire": True,
            "natural_calamities": True,
            "zero_depreciation": False,
        },
        "exclusions": [
            "Drunk driving",
            "Driving without valid license",
            "Intentional damage",
            "Mechanical breakdown",
            "Wear and tear",
            "Racing or speed testing",
        ],
        "ncb_discount": 20,
    },
    "POL-PROPERTY-001": {
        "policy_id": "POL-PROPERTY-001",
        "policy_type": "Property",
        "holder_name": "Suresh Kumar",
        "holder_id": "CUST-003",
        "property_address": "15, Park Avenue, Bengaluru - 560001",
        "sum_insured": 3000000.0,
        "premium": 8500.0,
        "deductible": 10000.0,
        "start_date": "2024-02-01",
        "end_date": "2030-01-31",
        "waiting_period_days": 0,
        "coverage_details": {
            "fire": True,
            "earthquake": True,
            "flood": True,
            "burglary": True,
            "structural_damage": True,
            "contents_cover": True,
            "contents_limit": 500000,
        },
        "exclusions": [
            "Wilful neglect",
            "War and nuclear risks",
            "Normal wear and tear",
            "Electrical/mechanical breakdown",
            "Pre-existing damage",
        ],
    },
    "POL-HEALTH-EXPIRED": {
        "policy_id": "POL-HEALTH-EXPIRED",
        "policy_type": "Health",
        "holder_name": "Test User",
        "holder_id": "CUST-004",
        "sum_insured": 300000.0,
        "premium": 10000.0,
        "deductible": 3000.0,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",  # EXPIRED
        "waiting_period_days": 30,
        "coverage_details": {"hospitalization": True},
        "exclusions": ["Cosmetic surgery"],
    },
}


class AISearchClient:
    def __init__(self):
        self.settings = get_settings()
        self._search_client = None
        self._index_client = None

    def _get_credential(self):
        if self.settings.search_admin_key:
            from azure.core.credentials import AzureKeyCredential
            return AzureKeyCredential(self.settings.search_admin_key)
        from azure.identity import DefaultAzureCredential
        return DefaultAzureCredential()

    def _get_search_client(self):
        if self._search_client is None and not self.settings.demo_mode:
            from azure.search.documents import SearchClient
            self._search_client = SearchClient(
                endpoint=self.settings.search_endpoint,
                index_name=self.settings.search_index_name,
                credential=self._get_credential(),
            )
        return self._search_client

    async def get_policy(self, policy_id: str) -> Optional[dict]:
        # Try local files first as source of truth
        try:
            from backend.data_seeder import POLICIES_DIR
            import os
            import json
            if os.path.exists(POLICIES_DIR):
                for filename in os.listdir(POLICIES_DIR):
                    if filename.endswith(".json"):
                        filepath = os.path.join(POLICIES_DIR, filename)
                        with open(filepath, "r", encoding="utf-8") as f:
                            p = json.load(f)
                            if p.get("policy_id") == policy_id:
                                return p
        except Exception as ex:
            logger.error("local_policy_lookup_failed", error=str(ex), policy_id=policy_id)

        if self.settings.demo_mode:
            await asyncio.sleep(0.1)
            return DEMO_POLICIES.get(policy_id)

        try:
            client = self._get_search_client()
            results = client.search(
                search_text=policy_id,
                filter=f"policy_id eq '{policy_id}'",
                top=1,
            )
            for r in results:
                return dict(r)
            return None
        except Exception as e:
            logger.error("policy_search_failed", error=str(e), policy_id=policy_id)
            return DEMO_POLICIES.get(policy_id)

    async def search_policy_terms(self, query: str, policy_type: str = None) -> list[dict]:
        # Try searching local policies first as the primary source of truth
        try:
            from backend.data_seeder import POLICIES_DIR
            import os
            import json
            local_policies = []
            if os.path.exists(POLICIES_DIR):
                for filename in os.listdir(POLICIES_DIR):
                    if filename.endswith(".json"):
                        with open(os.path.join(POLICIES_DIR, filename), "r", encoding="utf-8") as f:
                            local_policies.append(json.load(f))
            
            if local_policies:
                # Simple keyword search fallback
                query_words = set(query.lower().split())
                matched = []
                for p in local_policies:
                    if policy_type and p.get("policy_type") != policy_type:
                        continue
                    # score matches
                    score = 0
                    p_str = json.dumps(p).lower()
                    for word in query_words:
                        if word in p_str:
                            score += 1
                    if score > 0:
                        matched.append((score, p))
                matched.sort(key=lambda x: x[0], reverse=True)
                if matched:
                    return [p for score, p in matched[:3]]
                # If no keyword matches, return the first 3 filtered by policy_type to avoid empty results
                filtered = [p for p in local_policies if not policy_type or p.get("policy_type") == policy_type]
                if filtered:
                    return filtered[:3]
        except Exception as ex:
            logger.error("local_policy_search_failed", error=str(ex))

        if self.settings.demo_mode:
            await asyncio.sleep(0.2)
            results = []
            for policy in DEMO_POLICIES.values():
                if policy_type is None or policy.get("policy_type") == policy_type:
                    results.append(policy)
            return results[:3]

        try:
            client = self._get_search_client()
            filter_str = f"policy_type eq '{policy_type}'" if policy_type else None
            results = client.search(
                search_text=query,
                filter=filter_str,
                top=3,
                query_type="semantic",
                semantic_configuration_name="default",
            )
            return [dict(r) for r in results]
        except Exception as e:
            logger.error("policy_search_failed", error=str(e))
            # Final fallback to DEMO_POLICIES
            results = []
            for policy in DEMO_POLICIES.values():
                if policy_type is None or policy.get("policy_type") == policy_type:
                    results.append(policy)
            return results[:3]

    async def index_policy(self, policy: dict) -> bool:
        if self.settings.demo_mode:
            DEMO_POLICIES[policy["policy_id"]] = policy
            return True

        try:
            from azure.search.documents import SearchClient
            client = SearchClient(
                endpoint=self.settings.search_endpoint,
                index_name=self.settings.search_index_name,
                credential=self._get_credential(),
            )
            result = client.upload_documents(documents=[policy])
            return result[0].succeeded
        except Exception as e:
            logger.error("policy_index_failed", error=str(e))
            return False

    async def index_policies_bulk(self, policies: list[dict]) -> int:
        count = 0
        for policy in policies:
            if await self.index_policy(policy):
                count += 1
        return count
