import asyncio
import uuid
from typing import Optional
import structlog

from backend.config import get_settings
from backend.models.document import ExtractedDocument, DocumentType

logger = structlog.get_logger()

PREBUILT_MODEL_MAP = {
    DocumentType.HOSPITAL_BILL: "prebuilt-invoice",
    DocumentType.INVOICE: "prebuilt-invoice",
    DocumentType.RECEIPT: "prebuilt-receipt",
    DocumentType.PRESCRIPTION: "prebuilt-invoice",
    DocumentType.REPAIR_ESTIMATE: "prebuilt-invoice",
    DocumentType.ID_PROOF: "prebuilt-idDocument",
    DocumentType.POLICY_CARD: "prebuilt-idDocument",
    DocumentType.FIR: "prebuilt-layout",
    DocumentType.DISCHARGE_SUMMARY: "prebuilt-layout",
    DocumentType.DAMAGE_PHOTOS: "prebuilt-layout",
    DocumentType.UNKNOWN: "prebuilt-layout",
}

DEMO_EXTRACTIONS = {
    DocumentType.HOSPITAL_BILL: {
        "hospital_name": "Apollo Hospitals, Chennai",
        "patient_name": "Rahul Sharma",
        "admission_date": "2024-05-15",
        "discharge_date": "2024-05-20",
        "diagnosis": "Acute Appendicitis - Laparoscopic Surgery",
        "total_amount": 85000.0,
        "bill_number": "APL-2024-05-7823",
        "itemized_charges": [
            {"item": "Room Charges (5 days)", "amount": 25000},
            {"item": "Surgery Charges", "amount": 35000},
            {"item": "Medicines", "amount": 12000},
            {"item": "Lab Tests", "amount": 8000},
            {"item": "Miscellaneous", "amount": 5000},
        ],
    },
    DocumentType.FIR: {
        "fir_number": "FIR-2024-CH-4521",
        "police_station": "Velachery Police Station, Chennai",
        "date": "2024-05-18",
        "incident_description": "Road accident at OMR Junction. Vehicle TN09AB1234 rear-ended by TN05XY9876. No injuries. Vehicle damage to rear bumper and boot.",
        "vehicle_number": "TN09AB1234",
        "complainant_name": "Priya Nair",
    },
    DocumentType.REPAIR_ESTIMATE: {
        "garage_name": "Authorized Honda Service Center, Velachery",
        "vehicle_number": "TN09AB1234",
        "estimate_date": "2024-05-20",
        "total_estimate": 45000.0,
        "labor_charges": 8000.0,
        "parts_charges": 37000.0,
        "itemized_repairs": [
            {"item": "Rear Bumper Replacement", "amount": 18000},
            {"item": "Boot Lid Repair & Paint", "amount": 12000},
            {"item": "Taillight Assembly", "amount": 7000},
            {"item": "Labour & Alignment", "amount": 8000},
        ],
    },
    DocumentType.ID_PROOF: {
        "name": "Rahul Sharma",
        "id_number": "XXXX-XXXX-1234",
        "date_of_birth": "1988-03-15",
        "address": "42, Anna Nagar, Chennai - 600040",
        "document_type": "Aadhaar Card",
    },
    DocumentType.DISCHARGE_SUMMARY: {
        "patient_name": "Rahul Sharma",
        "hospital": "Apollo Hospitals, Chennai",
        "admission_date": "2024-05-15",
        "discharge_date": "2024-05-20",
        "diagnosis": "Acute Appendicitis",
        "procedure": "Laparoscopic Appendectomy",
        "surgeon": "Dr. S. Rajkumar, MS (Gen Surgery)",
        "discharge_condition": "Stable, advised rest for 2 weeks",
        "follow_up": "Review after 10 days",
    },
}


class DocumentIntelligenceClient:
    def __init__(self):
        self.settings = get_settings()
        self._client = None

    def _get_client(self):
        if self._client is None and not self.settings.demo_mode:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            if self.settings.doc_intelligence_key:
                from azure.core.credentials import AzureKeyCredential
                credential = AzureKeyCredential(self.settings.doc_intelligence_key)
            else:
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
            self._client = DocumentIntelligenceClient(
                endpoint=self.settings.doc_intelligence_endpoint,
                credential=credential,
            )
        return self._client

    async def extract_document(
        self,
        blob_url: str,
        doc_type: DocumentType,
        claim_id: str,
    ) -> ExtractedDocument:
        doc_id = str(uuid.uuid4())

        if self.settings.demo_mode:
            return await self._demo_extract(doc_id, claim_id, blob_url, doc_type)

        try:
            return await self._real_extract(doc_id, claim_id, blob_url, doc_type)
        except Exception as e:
            logger.error("document_extraction_failed", error=str(e), doc_type=doc_type)
            return ExtractedDocument(
                doc_id=doc_id,
                claim_id=claim_id,
                doc_type=doc_type,
                blob_url=blob_url,
                extraction_confidence=0.0,
                is_valid=False,
                validation_notes=f"Extraction failed: {str(e)}",
            )

    async def _real_extract(
        self, doc_id: str, claim_id: str, blob_url: str, doc_type: DocumentType
    ) -> ExtractedDocument:
        from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

        client = self._get_client()
        model_id = PREBUILT_MODEL_MAP.get(doc_type, "prebuilt-layout")

        poller = client.begin_analyze_document(
            model_id=model_id,
            analyze_request=AnalyzeDocumentRequest(url_source=blob_url),
        )
        result = poller.result()

        raw = {}
        normalized = {}
        confidence = 0.0

        if result.documents:
            doc = result.documents[0]
            confidence = doc.confidence or 0.0
            for field_name, field in (doc.fields or {}).items():
                raw[field_name] = {
                    "value": field.value_string or str(field.content or ""),
                    "confidence": field.confidence or 0.0,
                }
                normalized[field_name] = field.value_string or field.content

        if result.tables:
            normalized["tables"] = []
            for table in result.tables:
                table_data = []
                for cell in table.cells:
                    table_data.append({
                        "row": cell.row_index,
                        "col": cell.column_index,
                        "content": cell.content,
                    })
                normalized["tables"].append(table_data)

        return ExtractedDocument(
            doc_id=doc_id,
            claim_id=claim_id,
            doc_type=doc_type,
            blob_url=blob_url,
            extraction_model=model_id,
            raw_extraction=raw,
            normalized_fields=normalized,
            extraction_confidence=confidence,
            is_valid=confidence > 0.5,
            page_count=len(result.pages) if result.pages else 1,
        )

    async def _demo_extract(
        self, doc_id: str, claim_id: str, blob_url: str, doc_type: DocumentType
    ) -> ExtractedDocument:
        await asyncio.sleep(0.5)  # Simulate API latency
        normalized = DEMO_EXTRACTIONS.get(doc_type, {"note": "Demo document processed"})
        return ExtractedDocument(
            doc_id=doc_id,
            claim_id=claim_id,
            doc_type=doc_type,
            blob_url=blob_url,
            extraction_model="demo-prebuilt-invoice",
            raw_extraction=normalized,
            normalized_fields=normalized,
            extraction_confidence=0.94,
            is_valid=True,
            page_count=1,
        )
