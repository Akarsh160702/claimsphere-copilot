import json
import asyncio
from backend.agents.base_agent import BaseAgent
from backend.models.claim import ClaimContext, ClaimType, ClaimStatus
from backend.models.document import DocumentType, ExtractedDocument
from backend.tools.document_intelligence import DocumentIntelligenceClient

DOC_TYPE_MAP = {
    ClaimType.HEALTH: [DocumentType.HOSPITAL_BILL, DocumentType.DISCHARGE_SUMMARY, DocumentType.ID_PROOF],
    ClaimType.MOTOR: [DocumentType.FIR, DocumentType.REPAIR_ESTIMATE, DocumentType.ID_PROOF],
    ClaimType.PROPERTY: [DocumentType.DAMAGE_PHOTOS, DocumentType.REPAIR_ESTIMATE, DocumentType.ID_PROOF],
    ClaimType.TRAVEL: [DocumentType.ID_PROOF, DocumentType.RECEIPT],
}

NORMALIZE_SYSTEM_PROMPT = """You are an expert at normalizing extracted insurance document data.
Given raw OCR output, normalize and structure the key fields.
Remove noise, fix formatting, standardize dates to YYYY-MM-DD, standardize amounts to numbers.
Return clean, structured JSON only."""

NORMALIZE_USER_TEMPLATE = """Normalize this extracted document data:
Document Type: {doc_type}
Raw Extraction: {raw_data}

Return JSON with normalized, clean fields relevant for insurance claim processing.
Include a "confidence_score" (0-1) for the overall extraction quality."""


class DocumentAgent(BaseAgent):
    def __init__(self):
        super().__init__("DocumentAgent")
        self.doc_intelligence = DocumentIntelligenceClient()

    async def process(self, context: ClaimContext) -> ClaimContext:
        self.log("processing_documents", claim_id=context.claim_id,
                 doc_count=len(context.submission.document_urls))

        if not context.submission.document_urls:
            context.add_audit(
                agent_name=self.name,
                action="NO_DOCUMENTS",
                details={"message": "No documents submitted with claim"},
            )
            return context

        doc_types = DOC_TYPE_MAP.get(context.claim_type, [DocumentType.UNKNOWN])
        tasks = []

        for i, url in enumerate(context.submission.document_urls):
            doc_type = doc_types[i] if i < len(doc_types) else DocumentType.UNKNOWN
            tasks.append(self._extract_and_normalize(url, doc_type, context.claim_id))

        extracted_docs = await asyncio.gather(*tasks, return_exceptions=True)

        for result in extracted_docs:
            if isinstance(result, Exception):
                self.log_error("document_extraction_error", error=str(result))
                continue
            if result:
                context.extracted_documents.append(result.model_dump())

        context.add_audit(
            agent_name=self.name,
            action="DOCUMENTS_EXTRACTED",
            details={
                "total_documents": len(context.submission.document_urls),
                "extracted_count": len(context.extracted_documents),
                "avg_confidence": self._avg_confidence(context.extracted_documents),
                "document_types": [d.get("doc_type") for d in context.extracted_documents],
            },
        )
        self.log("documents_processed", claim_id=context.claim_id,
                 count=len(context.extracted_documents))
        return context

    async def _extract_and_normalize(
        self, url: str, doc_type: DocumentType, claim_id: str
    ) -> ExtractedDocument:
        extracted = await self.doc_intelligence.extract_document(url, doc_type, claim_id)

        if not self.settings.demo_mode and extracted.raw_extraction:
            try:
                normalized_raw = await self.call_llm(
                    messages=[
                        {"role": "system", "content": NORMALIZE_SYSTEM_PROMPT},
                        {"role": "user", "content": NORMALIZE_USER_TEMPLATE.format(
                            doc_type=doc_type.value,
                            raw_data=json.dumps(extracted.raw_extraction, indent=2)[:3000],
                        )},
                    ],
                    response_format={"type": "json_object"},
                )
                normalized = json.loads(normalized_raw)
                extracted.normalized_fields = normalized
                extracted.extraction_confidence = normalized.get(
                    "confidence_score", extracted.extraction_confidence
                )
            except Exception as e:
                self.log_error("normalization_failed", error=str(e))

        return extracted

    def _avg_confidence(self, docs: list[dict]) -> float:
        if not docs:
            return 0.0
        scores = [d.get("extraction_confidence", 0.0) for d in docs]
        return round(sum(scores) / len(scores), 3)
