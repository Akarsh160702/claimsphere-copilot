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

from collections import deque
logger = structlog.get_logger()

# In-memory store for demo mode / local dev
_demo_store: dict[str, dict] = {}
_demo_docs: dict[str, dict] = {}
_demo_logs: list[dict] = []

# Last 10 Dataverse write errors — exposed via /health/persist-errors
_dv_errors: deque = deque(maxlen=10)

# Map claim_id → Dataverse record GUID (for subsequent updates)
_claim_dv_id: dict[str, str] = {}

# Translate ClaimSphere domain values → the Choice option labels Copilot
# generated for this environment. Keys are lowercased domain values.
#   crcce_decision options: approved / denied / pending
#   crcce_status   options: open / closed / pending / rejected
#   crcce_claimtype options: accident / theft / fire / other
#   crcce_priority options: low / medium / high  (1:1, no alias needed)
_CHOICE_ALIASES: dict[str, dict[str, str]] = {
    "crcce_decision": {
        "approve": "approved", "approved": "approved",
        "reject": "denied", "rejected": "denied", "deny": "denied", "denied": "denied",
        "escalate": "pending", "escalated": "pending", "moreinfo": "pending",
    },
    "crcce_status": {
        "received": "open", "processing": "open", "new": "open", "submitted": "open",
        "pending information": "pending", "under human review": "pending",
        "pending_info": "pending", "under_review": "pending",
        "approved": "closed", "paid": "closed", "completed": "closed",
        "rejected": "rejected", "denied": "rejected",
        "escalated": "pending",
    },
    "crcce_claimtype": {
        "health": "other", "motor": "accident", "property": "fire", "travel": "other",
    },
}


class DataverseClient:
    # Cached primary-name logical column for crcce_claim (varies by environment)
    _primary_name_attr: Optional[str] = None
    # Cached Picklist (Choice) option maps: attr -> {label_lower: int_value}
    _picklist_cache: dict[str, dict] = {}

    def __init__(self):
        self.settings = get_settings()
        self._base_url = self.settings.dataverse_url.rstrip("/")
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    async def _get_picklist_map(self, token: str, attr: str) -> dict:
        """Fetch (and cache) the {label_lower: option_value} map for a Choice column."""
        if attr in DataverseClient._picklist_cache:
            return DataverseClient._picklist_cache[attr]
        mapping: dict = {}
        try:
            url = (
                f"{self._base_url}/api/data/v9.2/"
                f"EntityDefinitions(LogicalName='crcce_claim')/Attributes(LogicalName='{attr}')"
                f"/Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
                f"?$select=LogicalName&$expand=OptionSet($select=Options)"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers(token)) as resp:
                    body = await resp.json()
                    options = ((body.get("OptionSet") or {}).get("Options") or [])
                    for o in options:
                        label = ((o.get("Label") or {}).get("UserLocalizedLabel") or {}).get("Label", "")
                        val = o.get("Value")
                        if label and val is not None:
                            mapping[label.strip().lower()] = val
            DataverseClient._picklist_cache[attr] = mapping
        except Exception as e:
            logger.warning("picklist_map_failed", attr=attr, error=str(e))
        return mapping

    @staticmethod
    def _match_option(mapping: dict, value: str) -> Optional[int]:
        """Fuzzy-match a string value to a Choice option's integer value."""
        if not value or not mapping:
            return None
        v = str(value).strip().lower().replace("_", " ")
        if v in mapping:
            return mapping[v]
        for label, val in mapping.items():
            if label.startswith(v) or v.startswith(label) or v in label or label in v:
                return val
        return None

    async def _resolve_picklist(self, token: str, attr: str, value: str) -> Optional[int]:
        mapping = await self._get_picklist_map(token, attr)
        if not mapping or not value:
            return None
        # 1. Explicit alias for this domain value
        v = str(value).strip().lower()
        target = _CHOICE_ALIASES.get(attr, {}).get(v)
        if target and target in mapping:
            return mapping[target]
        # 2. Fall back to fuzzy match
        return self._match_option(mapping, value)

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
            "crcce_rationale":     (
                f"{str(d.get('claim_id') or '')[:16]}|{(d.get('rationale') or '')}"
            )[:100],
            "crcce_description":   (
                f"{str(d.get('claim_id') or '')[:16]}|[{claim_type}][{decision}][{fraud_risk}] "
                f"{d.get('description', '')}"
            )[:100],
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
            # Resolve Choice (Picklist) columns to their integer option values
            for attr, raw in (
                ("crcce_decision",  claim_data.get("decision")),
                ("crcce_status",    claim_data.get("status")),
                ("crcce_claimtype", claim_data.get("claim_type")),
                ("crcce_priority",  claim_data.get("priority")),
            ):
                if raw:
                    opt = await self._resolve_picklist(token, attr, raw)
                    if opt is not None:
                        payload[attr] = opt
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self._headers(token)) as resp:
                    if resp.status not in (200, 201, 204):
                        body = await resp.text()
                        logger.error("dataverse_create_claim_api_error",
                                     status=resp.status, body=body[:300])
                        _dv_errors.append({
                            "status": resp.status,
                            "payload_keys": list(payload.keys()),
                            "error": body[:500],
                            "ts": datetime.utcnow().isoformat(),
                        })
                        raise RuntimeError(f"Dataverse {resp.status}: {body[:200]}")
                    # OData-EntityId header is the most reliable source of the new GUID
                    import re as _re
                    entity_hdr = resp.headers.get("OData-EntityId", "")
                    m = _re.search(r'\(([0-9a-f-]{36})\)', entity_hdr)
                    dv_id = m.group(1) if m else ""
                    if not dv_id and resp.status != 204:
                        result = await resp.json()
                        dv_id = result.get("crcce_claimid", "")
                    if dv_id and claim_data.get("claim_id"):
                        _claim_dv_id[claim_data["claim_id"]] = dv_id
                    logger.info("dataverse_create_claim_ok",
                                claim_id=claim_data.get("claim_id"), dv_id=dv_id)
                    return dv_id or claim_data.get("claim_id", "")
        except Exception as e:
            logger.error("dataverse_create_claim_failed", error=str(e))
            claim_id = claim_data.get("claim_id", "FALLBACK")
            _demo_store[claim_id] = claim_data
            return claim_id

    async def update_claim(self, claim_id: str, updates: dict,
                           policy_id: str = "", claimant_name: str = "") -> bool:
        if self.settings.demo_mode:
            if claim_id in _demo_store:
                _demo_store[claim_id].update(updates)
                _demo_store[claim_id]["updated_at"] = datetime.utcnow().isoformat()
            return True

        try:
            token = await self._get_token()
            # Resolve Dataverse GUID: try cache first, then the claim_id prefix
            # stored in crcce_rationale. Policy+claimant is only a final fallback
            # because demo retries can create rows with the same person/policy.
            dv_id = _claim_dv_id.get(claim_id)
            if not dv_id:
                ref = claim_id[:16]
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self._base_url}/api/data/v9.2/crcce_claims"
                            f"?$select=crcce_claimid"
                            f"&$filter=startswith(crcce_rationale,'{ref}|')"
                            f"&$top=1",
                            headers=self._headers(token),
                        ) as r:
                            if r.status == 200:
                                rows = (await r.json()).get("value", [])
                                if rows:
                                    dv_id = rows[0].get("crcce_claimid")
                                    if dv_id:
                                        _claim_dv_id[claim_id] = dv_id
                except Exception:
                    pass
            if not dv_id:
                ref = claim_id[:16]
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self._base_url}/api/data/v9.2/crcce_claims"
                            f"?$select=crcce_claimid"
                            f"&$filter=startswith(crcce_description,'{ref}|')"
                            f"&$top=1",
                            headers=self._headers(token),
                        ) as r:
                            if r.status == 200:
                                rows = (await r.json()).get("value", [])
                                if rows:
                                    dv_id = rows[0].get("crcce_claimid")
                                    if dv_id:
                                        _claim_dv_id[claim_id] = dv_id
                except Exception:
                    pass
            if not dv_id:
                # Final fallback: query by policy_id + claimant_name.
                claimant = claimant_name
                if policy_id and claimant:
                    async with aiohttp.ClientSession() as session:
                        filter_url = (
                            f"{self._base_url}/api/data/v9.2/crcce_claims"
                            f"?$select=crcce_claimid"
                            f"&$filter=crcce_policyid eq '{policy_id}'"
                            f" and crcce_claimantname eq '{claimant}'"
                            f"&$top=1"
                        )
                        async with session.get(filter_url, headers=self._headers(token)) as r:
                            body = await r.json()
                            rows = body.get("value", [])
                            if rows:
                                dv_id = rows[0].get("crcce_claimid")
                                _claim_dv_id[claim_id] = dv_id
            if not dv_id and updates.get("decision"):
                # Compatibility fallback for rows created before we preserved
                # the claim_id marker. Demo operators reset before testing, so
                # the newest pending row is the intended human-review target.
                pending = await self._resolve_picklist(token, "crcce_decision", "pending")
                if pending is not None:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                f"{self._base_url}/api/data/v9.2/crcce_claims"
                                f"?$select=crcce_claimid"
                                f"&$filter=crcce_decision eq {pending}"
                                f"&$orderby=modifiedon desc"
                                f"&$top=1",
                                headers=self._headers(token),
                            ) as r:
                                if r.status == 200:
                                    rows = (await r.json()).get("value", [])
                                    if rows:
                                        dv_id = rows[0].get("crcce_claimid")
                                        if dv_id:
                                            _claim_dv_id[claim_id] = dv_id
                    except Exception:
                        pass
            if not dv_id:
                # Only surface to _dv_errors for real update attempts.
                # Pre-create _save_progress calls have no policy_id/claimant_name
                # and are expected to miss — don't pollute the error deque.
                if policy_id or claimant_name or updates.get("decision"):
                    _dv_errors.append({
                        "op": "update_guid_miss", "claim_id": claim_id,
                        "policy_id": policy_id, "claimant": claimant_name,
                        "updates": list(updates.keys()),
                        "ts": datetime.utcnow().isoformat(),
                    })
                logger.warning("dataverse_update_no_guid", claim_id=claim_id)
                return False
            mapped = {}
            if updates.get("decision"):
                opt = await self._resolve_picklist(token, "crcce_decision", updates["decision"])
                if opt is not None:
                    mapped["crcce_decision"] = opt        # real Choice column
            if updates.get("status"):
                opt = await self._resolve_picklist(token, "crcce_status", updates["status"])
                if opt is not None:
                    mapped["crcce_status"] = opt           # real Choice column
            if not mapped:
                return True
            url = f"{self._base_url}/api/data/v9.2/crcce_claims({dv_id})"
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=mapped, headers=self._headers(token)) as resp:
                    if resp.status not in (200, 204):
                        body = await resp.text()
                        logger.error("dataverse_update_api_error", status=resp.status, body=body[:300])
                        _dv_errors.append({
                            "op": "update", "status": resp.status,
                            "payload": mapped, "error": body[:400],
                            "ts": datetime.utcnow().isoformat(),
                        })
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
            primary = await self._get_primary_name_attr(token)
            url = (
                f"{self._base_url}/api/data/v9.2/crcce_claims"
                f"?$filter={primary} eq '{claim_id}'"
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

    async def delete_all_claims(self) -> dict:
        """Delete every row in the crcce_claims table. Returns a summary dict.

        Used by the admin reset endpoint to clear all demo/test data so the
        table starts clean before a fresh demo run.
        """
        if self.settings.demo_mode:
            n = len(_demo_store)
            _demo_store.clear()
            _claim_dv_id.clear()
            return {"deleted": n, "mode": "demo"}

        deleted = 0
        errors = []
        try:
            token = await self._get_token()
            async with aiohttp.ClientSession() as session:
                # Page through all rows collecting their GUIDs
                url = f"{self._base_url}/api/data/v9.2/crcce_claims?$select=crcce_claimid&$top=500"
                guids: list[str] = []
                while url:
                    async with session.get(url, headers=self._headers(token)) as resp:
                        body = await resp.json()
                        guids.extend(
                            row["crcce_claimid"]
                            for row in body.get("value", [])
                            if row.get("crcce_claimid")
                        )
                        url = body.get("@odata.nextLink")
                # Delete each row
                for gid in guids:
                    del_url = f"{self._base_url}/api/data/v9.2/crcce_claims({gid})"
                    async with session.delete(del_url, headers=self._headers(token)) as dresp:
                        if dresp.status in (200, 204):
                            deleted += 1
                        else:
                            errors.append(f"{gid}: HTTP {dresp.status}")
            _claim_dv_id.clear()
            return {"deleted": deleted, "found": len(guids), "errors": errors[:5], "mode": "live"}
        except Exception as e:
            logger.error("dataverse_delete_all_failed", error=str(e))
            return {"deleted": deleted, "error": str(e), "mode": "live"}

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
