# ClaimSphere API Reference

Complete API documentation for all endpoints.

## Base URLs

**Production**:
```
https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io
```

**Local Development**:
```
http://localhost:8000
```

**Interactive Documentation**:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

---

## Table of Contents

- [Health & Status](#health--status)
- [Claims Management](#claims-management)
- [Document Processing](#document-processing)
- [Support & Search](#support--search)
- [MCP (Model Context Protocol)](#mcp-model-context-protocol)
- [Admin & Utilities](#admin--utilities)

---

## Health & Status

### GET /health

Check system health and service connectivity.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-06-09T10:30:00Z",
  "services": {
    "openai": "connected",
    "document_intelligence": "connected",
    "ai_search": "connected",
    "blob_storage": "connected",
    "dataverse": "connected"
  },
  "version": "1.0.0"
}
```

**Use Case**: Monitoring, health checks, status dashboard

---

## Claims Management

### POST /claims/submit/sync

Submit a new claim and process synchronously.

**Request Body**:
```json
{
  "policy_id": "POL-HEALTH-001",
  "claim_type": "Health",
  "claimant_name": "Rajesh Kumar",
  "claimant_email": "rajesh@example.com",
  "incident_date": "2024-06-05",
  "claim_amount": 1500000,
  "description": "Cardiac bypass surgery at Apollo Hospital",
  "documents": [
    {
      "type": "hospital_bill",
      "url": "https://storage.blob.core.windows.net/claims/bill.pdf"
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "claim_id": "CLM-20260609-ABC123",
  "status": "Approved",
  "decision": {
    "result": "APPROVE",
    "approved_amount": 1450000,
    "deductions": [
      {"type": "Deductible", "amount": 50000}
    ],
    "confidence": 0.96,
    "rationale": "Claim is valid. Procedure covered under policy. All documents present. No fraud indicators detected.",
    "processing_time_seconds": 5.2
  },
  "pipeline_results": {
    "router": {"classification": "Health", "priority": "High"},
    "document": {"extraction_confidence": 0.96},
    "validation": {"is_valid": true, "coverage": "full"},
    "fraud": {"fraud_score": 15, "risk_level": "Low"},
    "missing_info": {"is_complete": true}
  },
  "timestamp": "2024-06-09T10:30:05Z"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/claims/submit/sync \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "POL-HEALTH-001",
    "claim_type": "Health",
    "claimant_name": "Test User",
    "claimant_email": "test@example.com",
    "incident_date": "2024-06-05",
    "claim_amount": 150000,
    "description": "Test claim"
  }'
```

---

### GET /claims/{claim_id}/status

Get the current status of a claim.

**Parameters**:
- `claim_id` (path): Claim identifier (e.g., CLM-20260609-ABC123)

**Response**:
```json
{
  "claim_id": "CLM-20260609-ABC123",
  "status": "Approved",
  "claim_type": "Health",
  "claimant_name": "Rajesh Kumar",
  "claim_amount": 1500000,
  "approved_amount": 1450000,
  "decision": "APPROVE",
  "rationale": "Claim is valid under policy POL-HEALTH-001...",
  "fraud_score": 15,
  "submitted_date": "2024-06-09T10:30:00Z",
  "processed_date": "2024-06-09T10:30:05Z",
  "processing_time_seconds": 5.2
}
```

**cURL Example**:
```bash
curl http://localhost:8000/claims/CLM-20260609-ABC123/status
```

---

### GET /claims

List all claims with optional filtering.

**Query Parameters**:
- `status` (optional): Filter by status (Processing, Approved, Rejected, etc.)
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset

**Response**:
```json
{
  "claims": [
    {
      "claim_id": "CLM-20260609-ABC123",
      "claimant_name": "Rajesh Kumar",
      "claim_type": "Health",
      "status": "Approved",
      "claim_amount": 1500000,
      "approved_amount": 1450000,
      "submitted_date": "2024-06-09T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**cURL Example**:
```bash
curl "http://localhost:8000/claims?status=Processing&limit=10"
```

---

### GET /claims/{claim_id}/fraud-analysis

Get detailed fraud analysis for a claim.

**Response**:
```json
{
  "claim_id": "CLM-20260609-ABC123",
  "fraud_score": 87,
  "risk_level": "High",
  "flags": [
    {
      "rule": "Amount Suspicion",
      "points": 25,
      "description": "Claim is 99.8% of policy limit"
    },
    {
      "rule": "Provider Check",
      "points": 20,
      "description": "Hospital not in verified network"
    },
    {
      "rule": "Frequency Check",
      "points": 20,
      "description": "Third claim in 4 months"
    }
  ],
  "recommendation": "Manual review required",
  "ai_analysis": "Multiple red flags detected. Recommend verification of hospital authenticity and claimant interview.",
  "requires_escalation": true
}
```

---

## Document Processing

### POST /documents/upload

Upload a document for a claim.

**Form Data**:
- `file`: Binary file data
- `claim_id`: Associated claim ID
- `document_type`: Type (hospital_bill, receipt, report, etc.)

**Response**:
```json
{
  "document_id": "DOC-20260609-XYZ",
  "blob_url": "https://storage.blob.core.windows.net/claims/CLM-20260609-ABC123/bill.pdf",
  "uploaded_at": "2024-06-09T10:30:00Z",
  "status": "Processing OCR"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@hospital_bill.pdf" \
  -F "claim_id=CLM-20260609-ABC123" \
  -F "document_type=hospital_bill"
```

---

### POST /documents/ocr

Extract data from a document using OCR.

**Request Body**:
```json
{
  "document_url": "https://storage.blob.core.windows.net/claims/bill.pdf",
  "document_type": "invoice"
}
```

**Response**:
```json
{
  "extracted_data": {
    "hospital_name": "Apollo Hospital",
    "patient_name": "Rajesh Kumar",
    "total_amount": 1500000,
    "date": "2024-06-08",
    "invoice_number": "INV-2024-12345",
    "procedure": "CABG Surgery"
  },
  "confidence": 0.96,
  "processing_time_ms": 2340
}
```

---

## Support & Search

### POST /support/search-policy

Search policy knowledge base using RAG.

**Request Body**:
```json
{
  "policy_id": "POL-HEALTH-001",
  "query": "Is cardiac surgery covered?"
}
```

**Response**:
```json
{
  "answer": "Yes, cardiac surgery is covered under Section 4.2 of your policy. Maximum sub-limit is ₹25 lakhs. Pre-authorization required within 24 hours of admission.",
  "sources": [
    {
      "section": "Section 4.2: Cardiac Procedures",
      "excerpt": "All major cardiac surgeries including CABG, valve replacement, angioplasty are covered..."
    }
  ],
  "confidence": 0.94
}
```

---

### POST /support/chat

Chat with the support agent.

**Request Body**:
```json
{
  "message": "What documents do I need for a health claim?",
  "session_id": "SESSION-123"
}
```

**Response**:
```json
{
  "reply": "For a health insurance claim, you'll need:\n1. Hospital bills and invoices\n2. Discharge summary\n3. Prescription from doctor\n4. Payment receipts\n5. Pre-authorization letter (if applicable)\n\nWould you like help with anything else?",
  "session_id": "SESSION-123"
}
```

---

## MCP (Model Context Protocol)

### GET /mcp

Discover available MCP tools.

**Response**:
```json
{
  "protocol": "model-context-protocol",
  "version": "1.0",
  "tools": [
    {
      "name": "submit_claim",
      "description": "Submit a new insurance claim",
      "input_schema": {
        "type": "object",
        "properties": {
          "policy_id": {"type": "string"},
          "claim_type": {"type": "string"},
          "claim_amount": {"type": "number"}
        },
        "required": ["policy_id", "claim_type", "claim_amount"]
      }
    },
    {
      "name": "get_claim_status",
      "description": "Get current status of a claim",
      "input_schema": {
        "type": "object",
        "properties": {
          "claim_id": {"type": "string"}
        },
        "required": ["claim_id"]
      }
    },
    {
      "name": "search_policy",
      "description": "Search policy knowledge base",
      "input_schema": {
        "type": "object",
        "properties": {
          "policy_id": {"type": "string"},
          "query": {"type": "string"}
        },
        "required": ["policy_id", "query"]
      }
    }
  ]
}
```

---

### POST /mcp/call

Call an MCP tool.

**Request Body**:
```json
{
  "tool": "submit_claim",
  "parameters": {
    "policy_id": "POL-HEALTH-001",
    "claim_type": "Health",
    "claimant_name": "Rajesh Kumar",
    "claim_amount": 1500000,
    "description": "Cardiac surgery"
  }
}
```

**Response**: Same as `/claims/submit/sync`

---

## Admin & Utilities

### POST /admin/seed-data

Seed database with sample data (development only).

**Response**:
```json
{
  "message": "Sample data seeded successfully",
  "policies_created": 4,
  "claims_created": 3
}
```

---

### GET /mock/policies

Get all demo policies (demo mode only).

**Response**:
```json
{
  "policies": [
    {
      "policy_id": "POL-HEALTH-001",
      "type": "Health",
      "sum_insured": 5000000,
      "holder_name": "Demo User"
    }
  ]
}
```

---

## Error Responses

All endpoints return standard error responses:

**400 Bad Request**:
```json
{
  "error": "Invalid request",
  "detail": "Missing required field: policy_id"
}
```

**404 Not Found**:
```json
{
  "error": "Not found",
  "detail": "Claim CLM-XXXXXXXX-XXX not found"
}
```

**500 Internal Server Error**:
```json
{
  "error": "Internal server error",
  "detail": "Azure OpenAI service unavailable"
}
```

---

## Rate Limits

- **Development**: No limits
- **Production**: 100 requests/minute per IP

---

## Authentication

Currently using API key authentication (planned for production).

**Header**:
```
Authorization: Bearer YOUR_API_KEY
```

---

For interactive testing, visit the Swagger UI at `/docs` endpoint.
