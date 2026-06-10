# ClaimSphere Architecture Documentation

## Table of Contents
- [System Architecture](#system-architecture)
- [7-Agent Pipeline](#7-agent-pipeline)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Integration Architecture](#integration-architecture)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Web Dashboard   │  │  Teams Chatbot   │  │ Power Apps UI    │  │
│  │  (React + Fluent)│  │ (Copilot Studio) │  │  (Canvas App)    │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
└───────────┼─────────────────────┼─────────────────────┼─────────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       API GATEWAY LAYER                              │
│                   FastAPI Backend (Python 3.11)                      │
│                 Azure Container Apps (Auto-scaling)                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ /claims     │  │ /documents  │  │ /support    │  │   /mcp    │ │
│  │ endpoints   │  │ upload API  │  │ chatbot API │  │  tools    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
└─────────┼────────────────┼────────────────┼───────────────┼────────┘
          │                │                │               │
          └────────────────┼────────────────┼───────────────┘
                           ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI ORCHESTRATION LAYER                            │
│                    7-Agent Pipeline (Orchestrator)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 1. RouterAgent        → Classify & Route (gpt-4o-mini)        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                           ▼                                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 2. DocumentAgent      → OCR & Extract (Doc Intelligence)      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                           ▼                                          │
│  ┌─────────────────────────┐    ┌──────────────────────────────┐   │
│  │ 3. ValidationAgent      │◄──►│ 4. FraudAgent                │   │
│  │    (gpt-4o-mini + RAG)  │    │    (rules + gpt-4o-mini)     │   │
│  └─────────────────────────┘    └──────────────────────────────┘   │
│         (Run in Parallel)                                            │
│                           ▼                                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 5. MissingInfoAgent   → Gap Detection (gpt-4o-mini)           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                           ▼                                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 6. AdjudicationAgent  → Final Decision (gpt-4o - premium)     │  │
│  │    Output: APPROVE / REJECT / ESCALATE                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                           ▼                                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 7. SupportAgent       → Customer Q&A (gpt-4o-mini + RAG)      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
└───────────────────────────────┬───────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       AZURE SERVICES LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ Azure OpenAI    │  │ Doc Intelligence│  │  AI Search      │     │
│  │ • gpt-4o        │  │ • OCR           │  │  • RAG Vector   │     │
│  │ • gpt-4o-mini   │  │ • Prebuilt      │  │  • Policy KB    │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ Blob Storage    │  │  Dataverse      │  │  Key Vault      │     │
│  │ • Documents     │  │  • Claims DB    │  │  • Secrets      │     │
│  │ • PDFs/Images   │  │  • Audit Logs   │  │  • API Keys     │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    POWER PLATFORM LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│  • Power Automate: Human escalation workflows                        │
│  • Microsoft Teams: Adaptive Cards for adjudication                 │
│  • Copilot Studio: Conversational AI chatbot                        │
│  • Dataverse: Structured data persistence                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7-Agent Pipeline

### Pipeline Flow with Timing

```
Claim Submitted
      ↓ (0.5s)
[1] RouterAgent
      ↓ (2.0s)
[2] DocumentAgent
      ↓
   ┌──┴──┐
   ↓(1s) ↓(1s)
[3] ValidationAgent    [4] FraudAgent
   (Parallel Processing)
   └──┬──┘
      ↓ (0.5s)
[5] MissingInfoAgent
      ↓ (1.0s)
[6] AdjudicationAgent
      ↓
   Decision Output
      ↓
[7] SupportAgent (Available for Q&A)
```

**Total Processing Time**: ~5 seconds

---

### Agent 1: RouterAgent

**File**: `backend/agents/router_agent.py`

**Purpose**: Classify and prioritize incoming claims

**Technology**: Azure OpenAI gpt-4o-mini

**Input**:
```json
{
  "claim_type": "Health",
  "claim_amount": 1500000,
  "policy_id": "POL-HEALTH-001",
  "description": "Cardiac bypass surgery"
}
```

**Processing**:
1. Analyzes claim description
2. Classifies type (Health/Motor/Property/Travel)
3. Determines priority based on amount and urgency
4. Routes to appropriate pipeline branch

**Output**:
```json
{
  "classification": "Health",
  "priority": "High",
  "confidence": 0.98,
  "routing": "health_pipeline",
  "estimated_complexity": "Medium"
}
```

---

### Agent 2: DocumentAgent

**File**: `backend/agents/document_agent.py`

**Purpose**: Extract structured data from documents using OCR

**Technology**: Azure AI Document Intelligence

**Supported Document Types**:
- Hospital bills and invoices
- Discharge summaries
- FIR (motor claims)
- Repair estimates
- Property damage reports
- Medical prescriptions

**Process**:
1. Retrieves document from Blob Storage
2. Sends to Document Intelligence API
3. Uses prebuilt models (invoice, receipt, health forms)
4. Extracts key-value pairs and tables
5. Returns structured JSON

**Output**:
```json
{
  "document_type": "hospital_bill",
  "extracted_data": {
    "hospital_name": "Apollo Hospital",
    "patient_name": "Rajesh Kumar",
    "date_of_admission": "2024-06-05",
    "date_of_discharge": "2024-06-08",
    "total_amount": 1500000,
    "procedure": "CABG Surgery",
    "room_charges": 150000,
    "surgery_charges": 800000,
    "medication": 250000
  },
  "confidence": 0.96,
  "extraction_time_ms": 2340
}
```

---

### Agent 3: ValidationAgent

**File**: `backend/agents/validation_agent.py`

**Purpose**: Validate claim eligibility and calculate covered limits against policy terms.

**Technology**: Azure OpenAI gpt-4o-mini + RAG (Azure AI Search or local fallback search)

**Input**: Extracted document data + Policy terms

**Processing**:
1. Checks policy active dates on the incident date (`start_date <= incident_date <= end_date`).
2. Confirms if the submitted claim type matches covered policy types.
3. Evaluates if the claim amount is within sum insured limits.
4. Checks for matching exclusion clauses in description/discharge summaries.
5. Applies sub-limits (e.g. room rent caps, maternity limits).
6. Computes initial covered amount and deductible.

**Output**:
```json
{
  "is_valid": true,
  "policy_active": true,
  "claim_type_covered": true,
  "within_sum_insured": true,
  "deductible_applicable": true,
  "coverage_amount": 42000.0,
  "deductible_amount": 5000.0,
  "exclusions_hit": [],
  "validation_notes": "Policy is active. Day-care covered. Deductible ₹5,000 applied.",
  "confidence": 0.95
}
```

---

### Agent 4: FraudAgent

**File**: `backend/agents/fraud_agent.py`

**Purpose**: Detect potential fraud indicators and calculate a risk score (0-100).

**Technology**: Rules Engine + Azure OpenAI gpt-4o-mini

**Input**: Claim details, policy history, extracted document summaries

**Processing**:
1. Runs rule checks for inception fraud (<30 days from start), round limit numbers, high motor claim values, low document extraction confidence, and vague description flags.
2. Performs cognitive comparison of document values against historical submissions to spot duplicates or inconsistencies.
3. Classifies risk level: LOW (score 0-30), MEDIUM (score 31-60), or HIGH (score 61-100).

**Output**:
```json
{
  "fraud_score": 15,
  "risk_level": "LOW",
  "flags": [],
  "reasoning": "No prior claims found, clean documentation, amount matches repair estimates.",
  "recommended_action": "proceed"
}
```

---

### Agent 5: MissingInfoAgent

**File**: `backend/agents/missing_info_agent.py`

**Purpose**: Identify missing mandatory documents or required data fields.

**Technology**: Azure OpenAI gpt-4o-mini

**Input**: Claim type, description, and list of extracted document types

**Processing**:
1. Checks if all mandatory documents for the claim type are present (e.g., FIR and repair estimate for Motor claims).
2. Verifies key fields are extracted within documents (e.g. diagnosis in a discharge summary).
3. Auto-drafts a customized, context-aware customer follow-up message when missing info is found.

**Output**:
```json
{
  "has_missing_info": false,
  "missing_fields": [],
  "follow_up_message": ""
}
```

---

### Agent 6: AdjudicationAgent

**File**: `backend/agents/adjudication_agent.py`

**Purpose**: Make final claims decisions (Approve, Reject, or Escalate) and compute exact final payout amounts.

**Technology**: Azure OpenAI gpt-4o (Premium model deployment) + Decision Rules Engine

**Input**: All outputs from ValidationAgent, FraudAgent, and MissingInfoAgent

**Processing**:
1. **Deterministic Rule Checks**: Checks if the claim is high-value (> ₹10L) or high-risk (fraud score >= 60) to automatically escalate to human queue; rejects if policy is inactive or exclusion is hit.
2. **GPT-4o Evaluation**: Ambiguous/nuanced claims (e.g. ₹5L to ₹10L) fall through to the premium GPT-4o model for a detailed, legally defensible adjudication review.
3. **Payout Calculation**: Calculates payout as `min(Claim, Coverage) - Deductible`.

**Output**:
```json
{
  "decision": "Approve",
  "claim_amount": 42000.0,
  "approved_amount": 42000.0,
  "deductible_applied": 5000.0,
  "final_payout": 37000.0,
  "rationale": "Claim approved via straight-through processing. Policy is active, claim type is covered, fraud score is low (8/100), and amount is within limits.",
  "confidence_score": 0.96,
  "supporting_evidence": ["Policy active", "Within auto-approval limit", "Fraud LOW"]
}
```

---

### Agent 7: SupportAgent

**File**: `backend/agents/support_agent.py`

**Purpose**: Powers the Customer Service Representative (CSR) co-pilot and chatbot interface.

**Technology**: Azure OpenAI gpt-4o-mini + RAG (Azure AI Search on Policy KB)

**Input**: CSR query, claim ID, policy ID

**Processing**:
1. Identifies and extracts referenced claim/policy IDs from natural language queries.
2. Fetches corresponding status, document, audit, and policy context from Dataverse.
3. Queries Azure AI Search for relevant policy terms matching the customer's coverage question.
4. Generates an empathetic response detailing claim timelines, explanation of AI decisions, or policy details, along with action recommendations for the CSR.

**Output**:
```json
{
  "answer": "Claim CLM-DEMO-001 has been approved for ₹37,000. Deductible of ₹5,000 was applied.",
  "claim_id": "CLM-DEMO-001",
  "sources": ["claim_data"],
  "suggested_actions": [
    "Check claim audit trail",
    "Inform customer of credit within 3 days"
  ]
}
```

---

