from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    HOSPITAL_BILL = "hospital_bill"
    DISCHARGE_SUMMARY = "discharge_summary"
    PRESCRIPTION = "prescription"
    FIR = "fir"
    REPAIR_ESTIMATE = "repair_estimate"
    VEHICLE_PHOTOS = "vehicle_photos"
    DAMAGE_PHOTOS = "damage_photos"
    PROPERTY_PHOTOS = "property_photos"
    ID_PROOF = "id_proof"
    POLICY_CARD = "policy_card"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    UNKNOWN = "unknown"


class ExtractedDocument(BaseModel):
    doc_id: str
    claim_id: str
    doc_type: DocumentType
    blob_url: str
    original_filename: str = ""
    extraction_model: str = ""
    raw_extraction: dict = Field(default_factory=dict)
    normalized_fields: dict = Field(default_factory=dict)
    extraction_confidence: float = 0.0
    is_valid: bool = True
    validation_notes: str = ""
    page_count: int = 1


class DocumentUploadRequest(BaseModel):
    claim_id: str
    doc_type: Optional[DocumentType] = DocumentType.UNKNOWN
    filename: str


class DocumentUploadResponse(BaseModel):
    doc_id: str
    blob_url: str
    upload_url: Optional[str] = None  # SAS URL for direct upload
    message: str


class HealthBillFields(BaseModel):
    hospital_name: Optional[str] = None
    patient_name: Optional[str] = None
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    diagnosis: Optional[str] = None
    total_amount: Optional[float] = None
    itemized_charges: list[dict] = Field(default_factory=list)
    bill_number: Optional[str] = None


class FIRFields(BaseModel):
    fir_number: Optional[str] = None
    police_station: Optional[str] = None
    date: Optional[str] = None
    incident_description: Optional[str] = None
    vehicle_number: Optional[str] = None
    complainant_name: Optional[str] = None


class RepairEstimateFields(BaseModel):
    garage_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    estimate_date: Optional[str] = None
    total_estimate: Optional[float] = None
    labor_charges: Optional[float] = None
    parts_charges: Optional[float] = None
    itemized_repairs: list[dict] = Field(default_factory=list)


class IDDocumentFields(BaseModel):
    name: Optional[str] = None
    id_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    document_type: Optional[str] = None  # Aadhaar, PAN, etc.
