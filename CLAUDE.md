# ClaimSphere Copilot — CLAUDE.md

## Project
**ClaimSphere Copilot** — AI-powered end-to-end insurance claims processing system.
Built for LTM x Microsoft Hack2Future 2026 hackathon by Team NEXORA.

## Working Directory
`E:\Nexora Project\hackathon-insurance-claim\`

## Company-Laptop / Deployment Workflow — READ THIS
This project is developed on a personal laptop (full tooling) but edited &
deployed from a **locked-down company laptop** (no admin, no PowerShell;
npm/pip/docker/az blocked; only VS Code + Copilot + git + browser work).
Therefore **nothing builds or runs on the company laptop** — all builds happen
in the cloud. See **`COMPANY-LAPTOP-WORKFLOW.md`** for the full model. In short:
- Transfer code via **GitHub** (`git push`/`pull`).
- **GitHub Actions** (`.github/workflows/`) build + deploy on every push to `main`:
  backend → Azure Container Apps (image built in ACR), frontend → Static Web Apps.
- Run `az`/`azd` from **Azure Cloud Shell** (browser), never locally.
- Need to actually run/build the app? Open a **GitHub Codespace** (`.devcontainer/`).
- On the company laptop, **Copilot** replaces Claude Code; do large refactors on the
  personal laptop with Claude Code, then push.

## Tech Stack
- **Backend**: Python 3.11 + FastAPI
- **AI/LLM**: Azure OpenAI (gpt-4o-mini for bulk, gpt-4o for adjudication ONLY)
- **Document AI**: Azure AI Document Intelligence (prebuilt models)
- **RAG**: Azure AI Search (Free tier)
- **Storage**: Azure Blob Storage (LRS Hot)
- **Database**: Dataverse (Power Platform, free with M365)
- **Hosting**: Azure Functions (Consumption plan)
- **UI**: Streamlit (demo) + Copilot Studio (production)
- **Workflow**: Power Automate + Teams (human-in-loop)

## Architecture
7 specialized agents in a pipeline:
1. RouterAgent (gpt-4o-mini) — classify + route
2. DocumentAgent (Azure Doc Intelligence) — OCR + extract
3. ValidationAgent (gpt-4o-mini + RAG) — policy validation
4. MissingInfoAgent (gpt-4o-mini) — gap detection
5. FraudAgent (rules + gpt-4o-mini) — fraud scoring
6. AdjudicationAgent (gpt-4o) — final decision (ONLY place using gpt-4o)
7. SupportAgent (gpt-4o-mini + RAG) — CSR Q&A

## Cost Constraints
- TOTAL BUDGET: $55 USD
- DO NOT use PTU/Provisioned-Managed Azure OpenAI (costs $2/hr = $48/day)
- USE ONLY Standard (On-Demand) deployments
- gpt-4o TPM cap: 10,000
- gpt-4o-mini TPM cap: 50,000

## Key Files
- `backend/main.py` — FastAPI app entry point
- `backend/orchestrator.py` — Agent pipeline coordinator
- `backend/agents/` — All 7 agent implementations
- `backend/tools/` — Azure service clients
- `streamlit_app.py` — Demo UI (run with `streamlit run streamlit_app.py`)
- `DEPLOYMENT.md` — Step-by-step Azure setup guide
- `.env.example` — Environment variables template

## Running Locally
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in Azure credentials
uvicorn backend.main:app --reload --port 8000
streamlit run streamlit_app.py
```

## Demo Mode
Set `DEMO_MODE=true` in .env to run with mock data (no Azure credentials needed).

## Claim Types Supported
- Health (hospital bills, discharge summaries)
- Motor (FIR, repair estimates)
- Property (damage photos, repair estimates)

## Scope Assumptions
- Synthetic/sample data only (no real PII)
- Mock APIs for CRM, Payment, Policy systems
- English language only
- Travel insurance excluded from demo
