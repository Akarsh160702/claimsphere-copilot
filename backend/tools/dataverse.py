"""
Dataverse client using Power Platform REST API (OData v4).
Falls back to in-memory store in demo mode.
"""
import asyncio
from datetime import datetime
from typing import Optional
import structlog
import aiohttp

from backend.config import get_settings

logger = structlog.get_logger()

# In-memory store for demo mode / local dev
_demo_store: dict[str, dict] = {}
_demo_docs: dict[str, dict] = {}
_demo_logs: list[dict] = []


class DataverseClient:
    def __init__(self):
        self.settings = get_settings()
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    async def _get_token(self) -> str:
        now = datetime.utcnow()
        if self._token and self._token_expiry and now < self._token_expiry:
            return self._token

        token_url = (
            f"https://login.microsoftonline.com/{self.settings.dataverse_tenant_id}"
            f"/oauth2/v2.0/token"
        )
        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.dataverse_client_id,
            "client_secret": self.settings.dataverse_client_secret,
            "scope": f"{self.settings.dataverse_url}/.default",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as resp:
                result = await resp.json()
                self._token = result["access_token"]
                self._token_expiry = datetime.utcnow()
                return self._token

    def _headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
            "Prefer": "return=representation",
        }

    async def create_claim(self, claim_data: dict) -> str:
        if self.settings.demo_mode:
            claim_id = claim_data.get("claim_id", f"CLM-DEMO-{len(_demo_store)}")
            _demo_store[claim_id] = {**claim_data, "created_at": datetime.utcnow().isoformat()}
            return claim_id

        try:
            token = await self._get_token()
            url = f"{self.settings.dataverse_url}/api/data/v9.2/cs_claims"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=claim_data, headers=self._headers(token)) as resp:
                    result = await resp.json()
                    return result.get("cs_claimid", claim_data.get("claim_id"))
        except Exception as e:
            logger.error("dataverse_create_claim_failed", error=str(e))
            claim_id = claim_data.get("claim_id", "FALLBACK")
            _demo_store[claim_id] = claim_data
            return claim_id

    async def update_claim(self, claim_id: str, updates: dict) -> bool:
        if self.settings.demo_mode:
            if claim_id in _demo_store:
                _demo_store[claim_id].update(updates)
                _demo_store[claim_id]["updated_at"] = datetime.utcnow().isoformat()
            return True

        try:
            token = await self._get_token()
            url = f"{self.settings.dataverse_url}/api/data/v9.2/cs_claims({claim_id})"
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=updates, headers=self._headers(token)) as resp:
                    return resp.status in (200, 204)
        except Exception as e:
            logger.error("dataverse_update_claim_failed", error=str(e))
            if claim_id in _demo_store:
                _demo_store[claim_id].update(updates)
            return False

    async def get_claim(self, claim_id: str) -> Optional[dict]:
        if self.settings.demo_mode:
            return _demo_store.get(claim_id)

        try:
            token = await self._get_token()
            url = (
                f"{self.settings.dataverse_url}/api/data/v9.2/cs_claims"
                f"?$filter=cs_claimnumber eq '{claim_id}'"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers(token)) as resp:
                    result = await resp.json()
                    values = result.get("value", [])
                    return values[0] if values else None
        except Exception as e:
            logger.error("dataverse_get_claim_failed", error=str(e))
            return _demo_store.get(claim_id)

    async def get_all_claims(self) -> list[dict]:
        if self.settings.demo_mode:
            return list(_demo_store.values())

        try:
            token = await self._get_token()
            url = f"{self.settings.dataverse_url}/api/data/v9.2/cs_claims?$orderby=createdon desc&$top=100"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers(token)) as resp:
                    result = await resp.json()
                    return result.get("value", [])
        except Exception as e:
            logger.error("dataverse_get_all_claims_failed", error=str(e))
            return list(_demo_store.values())

    async def create_document_record(self, doc_data: dict) -> str:
        if self.settings.demo_mode:
            doc_id = doc_data.get("doc_id", f"DOC-{len(_demo_docs)}")
            _demo_docs[doc_id] = doc_data
            return doc_id

        try:
            token = await self._get_token()
            url = f"{self.settings.dataverse_url}/api/data/v9.2/cs_claimdocuments"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=doc_data, headers=self._headers(token)) as resp:
                    result = await resp.json()
                    return result.get("cs_claimdocumentid", doc_data.get("doc_id"))
        except Exception as e:
            logger.error("dataverse_create_doc_failed", error=str(e))
            doc_id = doc_data.get("doc_id", "FALLBACK")
            _demo_docs[doc_id] = doc_data
            return doc_id

    async def create_audit_log(self, log_data: dict) -> None:
        if self.settings.demo_mode:
            _demo_logs.append({**log_data, "timestamp": datetime.utcnow().isoformat()})
            return

        try:
            token = await self._get_token()
            url = f"{self.settings.dataverse_url}/api/data/v9.2/cs_claimauditlogs"
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=log_data, headers=self._headers(token))
        except Exception as e:
            logger.error("dataverse_audit_log_failed", error=str(e))
            _demo_logs.append(log_data)

    def get_demo_claims(self) -> list[dict]:
        return list(_demo_store.values())

    def get_demo_logs(self) -> list[dict]:
        return _demo_logs
