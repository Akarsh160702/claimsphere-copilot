/**
 * TypeScript mirrors of the backend Pydantic models
 * (backend/models/claim.py). Keep these in sync with the API.
 */

export type ClaimType = "Health" | "Motor" | "Property" | "Travel";

export type ClaimStatus =
  | "Received"
  | "Processing"
  | "Pending Information"
  | "Under Human Review"
  | "Approved"
  | "Rejected"
  | "Escalated";

export type ClaimPriority = "Low" | "Medium" | "High";

export type Channel = "Web" | "Email" | "Teams" | "Phone" | "CSR";

export type Decision = "Approve" | "Reject" | "Escalate";

export interface ClaimantInfo {
  name: string;
  email: string;
  phone: string;
  id_number?: string | null;
  address?: string | null;
}

export interface ClaimSubmission {
  policy_id: string;
  claimant: ClaimantInfo;
  claim_type?: ClaimType | null;
  claim_amount: number;
  incident_date: string;
  description: string;
  channel: Channel;
  document_urls: string[];
}

export interface FraudResult {
  fraud_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | string;
  flags: string[];
  reasoning: string;
}

export interface AdjudicationResult {
  decision: Decision;
  claim_amount: number;
  approved_amount: number;
  deductible_applied: number;
  final_payout: number;
  rationale: string;
  confidence_score: number;
  supporting_evidence: string[];
  escalation_reason?: string | null;
  rejection_reason?: string | null;
}

export interface AuditEntry {
  agent_name: string;
  action: string;
  timestamp: string;
  details: Record<string, unknown>;
}

/** Shape returned by GET /claims/ (list view). */
export interface ClaimListItem {
  claim_id: string;
  status: ClaimStatus | null;
  claim_type: ClaimType | null;
  claim_amount: number | null;
  claimant_name: string | null;
  submitted_at: string | null;
  decision: Decision | null;
  final_payout: number | null;
  /** Derived client-side (not always present from backend). */
  fraud_score?: number;
  channel?: Channel;
}

/** Shape returned by POST /claims/submit. */
export interface ClaimResponse {
  claim_id: string;
  status: ClaimStatus;
  message: string;
  tracking_url?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  demo_mode: boolean;
  team: string;
  hackathon: string;
}

export interface SupportAnswer {
  answer: string;
  [k: string]: unknown;
}

/** Aggregated KPIs computed from the claim list. */
export interface DashboardMetrics {
  total: number;
  approved: number;
  rejected: number;
  escalated: number;
  pending: number;
  stpRate: number;
  totalPayout: number;
  avgFraud: number;
  byType: Record<ClaimType, number>;
  byChannel: Record<string, number>;
}
