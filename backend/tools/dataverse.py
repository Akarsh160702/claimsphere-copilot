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
    # Cached primary-name logical column for crcce_claim (varies by environment)
    _primary_name_attr: Optional[str] = None

    def __init__(self):
        self.settings = get_settings()
        self._base_url = self.settings.dataverse_url.rstrip("/")
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    async def _get_primary_name_attr(self, token: str) -> str:
        """Discover (and cache) the primary name column of crcce_claim."""
        if DataverseClient._primary_name_attr:
            return DataverseClient._primary_name_attr
        try:
            url = (
                f"{self._base_url}/api/data/v9.2/"
                "EntityDefinitions(LogicalName='crcce_claim')?$select=PrimaryNameAttribute"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers(token)) as resp:
                    meta = await resp.json()
                    attr = meta.get("PrimaryNameAttribute", "crcce_name")
                    DataverseClient._primary_name_attr = attr
                    return attr
        except Exception as e:
            logger.warning("dataverse_primary_name_lookup_failed", error=str(e))
            return "crcce_name"

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
            "scope": f"{self._base_url}/.default",
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

    @staticmethod
    def _map_claim(d: dict) -> dict:
        """Translate orchestrator keys → verified crcce_ Dataverse column names.

        Columns confirmed from EntityDefinitions metadata:
          String:   crcce_name (primary), crcce_policyid, crcce_claimantname, crcce_claimantemail
          Money:    crcce_claimamount, crcce_approvedamount
          Decimal:  crcce_fraudscore
          DateTime: crcce_incidentdate  (needs full ISO-8601, not date-only)
          Memo:     crcce_rationale, crcce_description
          Picklist: crcce_claimtype, crcce_status, crcce_decision, crcce_priority (skipped — Int32)
        """
        incident = d.get("incident_date", "")
        # Dataverse DateTime requires full ISO-8601
        if incident and len(incident) == 10:
            incident = incident + "T00:00:00Z"

        claim_type = d.get("claim_type", "")
        status     = d.get("status", "")
        decision   = d.get("decision", "")
        priority   = d.get("priority", "")
        fraud_risk = d.get("fraud_risk_level", "")

        # Primary name column (claim number) is added separately in create_claim,
        # since its logical name varies by environment.
        return {
            "crcce_policyid":      d.get("policy_id"),
            "crcce_claimantname":  d.get("claimant_name"),
            "crcce_claimantemail": d.get("claimant_email"),
            "crcce_claimamount":   d.get("claim_amount"),
            "crcce_approvedamount":d.get("approved_amount"),
            "crcce_fraudscore":    float(d["fraud_score"]) if d.get("fraud_score") is not None else None,
            "crcce_incidentdate":  incident or None,
            "crcce_rationale":     d.get("rationale"),
            "crcce_description":   (
                f"[{claim_type}] [{priority}] Status: {status} | "
                f"Decision: {decision} | Fraud Risk: {fraud_risk} | "
                f"{d.get('description', '')}"
            ),
        }

    @staticmethod
    def _map_doc(d: dict) -> dict:
        return {
            "crcce_claimid":      d.get("claim_id"),
            "crcce_documenttype": d.get("document_type", d.get("doc_type", "unknown")),
            "crcce_bloburl":      d.get("blob_url", d.get("url", "")),
            "crcce_extracteddata":str(d.get("extracted_data", d.get("data", ""))),
        }

    @staticmethod
    def _map_audit(d: dict) -> dict:
        return {
            "crcce_claimid":   d.get("claim_id"),
            "crcce_agentname": d.get("agent_name"),
            "crcce_action":    d.get("action"),
            "crcce_details":   d.get("details", ""),
        }

    async def create_claim(self, claim_data: dict) -> str:
        if self.settings.demo_mode:
            claim_id = claim_data.get("claim_id", f"CLM-DEMO-{len(_demo_store)}")
            _demo_store[claim_id] = {**claim_data, "created_at": datetime.utcnow().isoformat()}
            return claim_id

        try:
            token = await self._get_token()
            url = f"{self._base_url}/api/data/v9.2/crcce_claims"
            payload = {k: v for k, v in self._map_claim(claim_data).items() if v is not None}
            # Inject claim_id under the primary-name column only if it's not
            # already mapped (e.g. in this env the primary is crcce_claimantname
            # which is already mapped — don't overwrite the actual claimant name).
            primary = await self._get_primary_name_attr(token)
            if primary not in payload:
                payload[primary] = claim_data.get("claim_id")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self._headers(token)) as resp:
                    if resp.status not in (200, 201, 204):
                        body = await resp.text()
                        logger.error("dataverse_create_claim_api_error",
                                     status=resp.status, body=body[:300])
                        raise RuntimeError(f"Dataverse {resp.status}: {body[:200]}")
                    result = await resp.json() if resp.status != 204 else {}
                    return result.get("crcce_claimid", claim_data.get("claim_id", ""))
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
            url = f"{self._base_url}/api/data/v9.2/crcce_claims({claim_id})"
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
                f"{self._base_url}/api/data/v9.2/crcce_claims"
                f"?$filter=crcce_claimnumber eq '{claim_id}'"
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
            url = f"{self._base_url}/api/data/v9.2/crcce_claims?$orderby=createdon desc&$top=100"
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
            url = f"{self._base_url}/api/data/v9.2/crcce_claimdocuments"
            payload = {k: v for k, v in self._map_doc(doc_data).items() if v is not None}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self._headers(token)) as resp:
                    result = await resp.json()
                    return result.get("crcce_claimdocumentid", doc_data.get("doc_id", ""))
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
            url = f"{self._base_url}/api/data/v9.2/crcce_claimauditlogs"
            payload = {k: v for k, v in self._map_audit(log_data).items() if v is not None}
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=payload, headers=self._headers(token))
        except Exception as e:
            logger.error("dataverse_audit_log_failed", error=str(e))
            _demo_logs.append(log_data)

    def get_demo_claims(self) -> list[dict]:
        return list(_demo_store.values())

    def get_demo_logs(self) -> list[dict]:
        return _demo_logs
