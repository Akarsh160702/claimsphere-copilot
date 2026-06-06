# ClaimSphere Copilot
### LTM x Microsoft Hack2Future 2026 — Team NEXORA

AI-powered end-to-end insurance claims processing system built on Azure AI Foundry, Power Platform, and Model Context Protocol.

---

## Architecture

```
Claimant / CSR
      │
      ▼
ClaimSphere Web UI  ◄──────────────────────────────────┐
(React + Fluent UI)                                     │
      │                                                 │
      ▼                                                 │
FastAPI Backend  ─── 7-Agent AI Pipeline ───────────────┤
(Azure Container Apps)                                  │
      │                                                 │
      ├── RouterAgent        (gpt-4o-mini)             │
      ├── DocumentAgent      (Azure Doc Intelligence)  │
      ├── ValidationAgent    (gpt-4o-mini + RAG)       │
      ├── FraudAgent         (rules + gpt-4o-mini)     │
      ├── MissingInfoAgent   (gpt-4o-mini)             │
      ├── AdjudicationAgent  (gpt-4o — final decision) │
      └── SupportAgent       (gpt-4o-mini + RAG)       │
              │                                         │
              ├── Azure AI Search (policy RAG)          │
              ├── Azure Blob Storage (documents)        │
              ├── Dataverse (persistence)               │
              │                                         │
              ├── Power Automate ──► Teams Adaptive Card│
              │         Approve/Reject buttons ─────────┘
              │
              └── MCP Server (/mcp)
                      │
                      └── Copilot Studio Agent
                               │
                               └── Microsoft Teams Bot
```

---

## Microsoft Stack Used

| Service | Role |
|---|---|
| **Azure OpenAI** (gpt-4o, gpt-4o-mini) | 7-agent AI pipeline |
| **Azure AI Document Intelligence** | OCR & document extraction |
| **Azure AI Search** | Policy knowledge base (RAG) |
| **Azure Blob Storage** | Claim document storage |
| **Azure Container Apps** | Backend hosting |
| **Azure Static Web Apps** | Frontend hosting |
| **Azure Application Insights** | Distributed tracing & monitoring |
| **Power Automate** | Escalation workflow automation |
| **Microsoft Teams** | Human-in-loop adjudication via Adaptive Cards |
| **Copilot Studio** | Conversational AI agent |
| **Dataverse** | Structured claims data persistence |
| **Model Context Protocol (MCP)** | Tool exposure to AI assistants |

---

## Key Features

### 7-Agent Pipeline
Claims flow through 6 specialized AI agents in under 5 seconds:
1. **Router** — classify claim type, set priority
2. **Document** — OCR + extract structured fields
3. **Validation + Fraud** — run in parallel (policy check + fraud scoring)
4. **Missing Info** — detect and request gaps
5. **Adjudication** — final Approve / Reject / Escalate decision

### Human-in-the-Loop (Teams)
High-risk claims trigger a Power Automate flow that posts an Adaptive Card to a Teams channel. Adjudicators click **Approve** or **Reject** — the decision is applied to the live claim in real time.

### MCP Server
ClaimSphere exposes 6 tools via the Model Context Protocol:
- `submit_claim` — run the full AI pipeline from any MCP client
- `get_claim_status` — live status + decision + fraud score
- `search_policy` — query the RAG knowledge base
- `check_coverage` — coverage eligibility check
- `list_claims` — pipeline overview
- `get_fraud_score` — fraud analysis detail

Any MCP client (Copilot Studio, Claude Desktop, VS Code Copilot) can connect to `/mcp`.

### Copilot Studio Agent
A Teams bot backed by the MCP server. Users can ask:
- "Submit a health claim for ₹15L"
- "What is the status of CLM-20260606-XXXXX?"
- "Am I covered for cardiac surgery under POL-HEALTH-001?"

---

## Live Endpoints

| URL | Description |
|---|---|
| `https://orange-beach-00e4c8e0f.7.azurestaticapps.net` | Web UI |
| `https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io` | Backend API |
| `.../docs` | Swagger UI |
| `.../health` | Integration status dashboard |
| `.../mcp` | MCP server (tool discovery) |

---

## Quick Demo

**Claims Pipeline:**
1. Open the web UI → New Claim
2. Submit: Policy `POL-HEALTH-001`, Type Health, Amount ₹15,00,000
3. Watch the 6-step AI pipeline run in real time
4. Escalated claims → Teams card appears in **Fraud Alerts** channel
5. Click Approve in Teams → ClaimSphere auto-applies the decision

**Copilot Studio / MCP:**
1. Open ClaimSphere Assistant in Copilot Studio test panel
2. Type: *Submit a health claim for Raj Kumar, policy POL-HEALTH-001, amount 1500000, description "Cardiac bypass surgery"*
3. Agent calls `submit_claim` MCP tool → returns AI decision
4. Type: *Check the status of that claim*

---

## Local Development

```bash
git clone https://github.com/Akarsh160702/claimsphere-copilot
cd claimsphere-copilot

# Backend
pip install -r requirements.txt
cp .env.example .env   # fill credentials
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Set `DEMO_MODE=true` in `.env` to run with mock data (no Azure credentials needed).

---

## Team

**NEXORA** — LTM x Microsoft Hack2Future 2026
