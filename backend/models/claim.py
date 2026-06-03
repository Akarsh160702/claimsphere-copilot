from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ClaimType(str, Enum):
    HEALTH = "Health"
    MOTOR = "Motor"
    PROPERTY = "Property"
    TRAVEL = "Travel"


class ClaimStatus(str, Enum):
    RECEIVED = "Received"
    PROCESSING = "Processing"
    PENDING_INFO = "Pending Information"
    UNDER_REVIEW = "Under Human Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    ESCALATED = "Escalated"


class ClaimPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Channel(str, Enum):
    WEB = "Web"
    EMAIL = "Email"
    TEAMS = "Teams"
    PHONE = "Phone"
    CSR = "CSR"


class ClaimantInfo(BaseModel):
    name: str
    email: str
    phone: str
    id_number: Optional[str] = None  # Aadhaar / PAN
    address: Optional[str] = None


class ClaimSubmission(BaseModel):
    """Inbound claim from any channel."""
    policy_id: str
    claimant: ClaimantInfo
    claim_type: Optional[ClaimType] = None  # Auto-detected if not provided
    claim_amount: float
    incident_date: str  # ISO date string
    description: str
    channel: Channel = Channel.WEB
    document_urls: list[str] = Field(default_factory=list)  # Blob URLs


class ValidationResult(BaseModel):
    is_valid: bool
    policy_active: bool
    claim_type_covered: bool
    within_sum_insured: bool
    deductible_applicable: bool
    exclusions_hit: list[str] = Field(default_factory=list)
    coverage_amount: float = 0.0
    deductible_amount: float = 0.0
    validation_notes: str = ""
    confidence: float = 1.0


class FraudResult(BaseModel):
    fraud_score: int = Field(ge=0, le=100)
    risk_level: str  # LOW / MEDIUM / HIGH
    flags: list[str] = Field(default_factory=list)
    reasoning: str = ""


class MissingInfoResult(BaseModel):
    has_missing_info: bool
    missing_fields: list[str] = Field(default_factory=list)
    follow_up_message: str = ""
    follow_up_channel: str = "email"


class Decision(str, Enum):
    APPROVE = "Approve"
    REJECT = "Reject"
    ESCALATE = "Escalate"


class AdjudicationResult(BaseModel):
    decision: Decision
    claim_amount: float
    approved_amount: float = 0.0
    deductible_applied: float = 0.0
    final_payout: float = 0.0
    rationale: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    escalation_reason: Optional[str] = None
    rejection_reason: Optional[str] = None


class AuditEntry(BaseModel):
    agent_name: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: dict = Field(default_factory=dict)


class ClaimContext(BaseModel):
    """Shared context object that flows through the agent pipeline."""
    claim_id: str = Field(default_factory=lambda: f"CLM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    submission: ClaimSubmission
    claim_type: Optional[ClaimType] = None
    priority: ClaimPriority = ClaimPriority.MEDIUM
    status: ClaimStatus = ClaimStatus.RECEIVED
    policy_data: Optional[dict] = None
    extracted_documents: list[dict] = Field(default_factory=list)
    validation_result: Optional[ValidationResult] = None
    fraud_result: Optional[FraudResult] = None
    missing_info_result: Optional[MissingInfoResult] = None
    adjudication_result: Optional[AdjudicationResult] = None
    audit_trail: list[AuditEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None

    def add_audit(self, agent_name: str, action: str, details: dict = None):
        self.audit_trail.append(AuditEntry(
            agent_name=agent_name,
            action=action,
            details=details or {}
        ))
        self.updated_at = datetime.utcnow()


class ClaimResponse(BaseModel):
    """API response for claim submission."""
    claim_id: str
    status: ClaimStatus
    message: str
    tracking_url: Optional[str] = None


class ClaimStatusResponse(BaseModel):
    """API response for claim status query."""
    claim_id: str
    status: ClaimStatus
    claim_type: Optional[ClaimType]
    priority: ClaimPriority
    submitted_at: datetime
    updated_at: datetime
    adjudication: Optional[AdjudicationResult] = None
    missing_info: Optional[MissingInfoResult] = None
    fraud_summary: Optional[str] = None
    audit_trail: list[AuditEntry] = Field(default_factory=list)
