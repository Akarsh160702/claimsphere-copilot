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

