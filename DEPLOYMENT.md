# ClaimSphere Copilot — Azure Deployment Guide
## Team NEXORA | Step-by-Step from Zero to Live

---

## OVERVIEW

You will provision these resources in order:
1. Resource Group
2. Azure OpenAI (Standard — NOT PTU)
3. Azure AI Document Intelligence
4. Azure AI Search (Free tier)
5. Azure Storage Account
6. Azure Key Vault
7. Azure Functions App
8. Power Platform (Dataverse + Copilot Studio + Power Automate)

**Total estimated cost for 10-day build: ~$3–5** (well within $55 budget)

---

## PREREQUISITES

Before starting, open your lab environment:
1. Go to: https://experience.cloudlabs.ai
2. Log in and navigate to your HackToFuture lab
3. Click "Launch Azure Portal" to get your sandbox credentials
4. Sign in to https://portal.azure.com with the lab credentials

---

## STEP 1 — CREATE RESOURCE GROUP

> A Resource Group is a container for all your Azure resources.

1. In Azure Portal, click **"Create a resource"** (top left, + button)
2. Search for **"Resource Group"** → Click **Create**
3. Fill in:
   - **Subscription**: Your lab subscription (auto-selected)
   - **Resource group name**: `rg-claimsphere-hack`
   - **Region**: `East US` ← IMPORTANT: GPT-4o available here
4. Click **Review + Create** → **Create**
5. Wait ~30 seconds for deployment to complete

---

## STEP 2 — AZURE OPENAI (⚠️ CRITICAL — READ CAREFULLY)

> ⚠️ WARNING: NEVER select PTU/Provisioned-Managed — it costs $2/hr = $48/day!

### 2A. Create the OpenAI Resource

1. Click **"Create a resource"**
2. Search **"Azure OpenAI"** → Select it → Click **Create**
3. Fill in:
   - **Subscription**: Lab subscription
   - **Resource group**: `rg-claimsphere-hack`
   - **Region**: `East US` (required for GPT-4o access)
   - **Name**: `oai-claimsphere` (must be globally unique — add your initials if taken)
   - **Pricing tier**: `Standard S0`
4. Click **Next: Network** → Leave defaults → **Next: Tags** → **Review + Create** → **Create**
5. Wait 2–3 minutes for deployment

### 2B. Deploy Models (STANDARD ONLY)

1. Go to your new OpenAI resource → Click **"Go to Azure AI Foundry portal"** (or **"Model deployments"**)
2. Click **"Deploy model"** → **"Deploy base model"**

**Deployment 1 — GPT-4o-mini (bulk agent work):**
- Model: `gpt-4o-mini`
- Deployment name: `gpt-4o-mini` (exact — matches .env)
- Deployment type: **Standard** ← NOT Provisioned/PTU
- Tokens per minute: `50,000` (set this cap!)
- Click **Deploy**

**Deployment 2 — GPT-4o (adjudication only):**
- Model: `gpt-4o`
- Deployment name: `gpt-4o` (exact — matches .env)
- Deployment type: **Standard** ← NOT Provisioned/PTU
- Tokens per minute: `10,000` (set this cap — limits cost!)
- Click **Deploy**

### 2C. Copy Credentials

1. Go back to your OpenAI resource (not AI Foundry portal)
2. Left sidebar → **"Keys and Endpoint"**
3. Copy:
   - **KEY 1** → paste into `.env` as `AZURE_OPENAI_API_KEY`
   - **Endpoint** (e.g., `https://oai-claimsphere.openai.azure.com/`) → `AZURE_OPENAI_ENDPOINT`

---

## STEP 3 — AZURE AI DOCUMENT INTELLIGENCE

1. Click **"Create a resource"**
2. Search **"Document Intelligence"** (also shows as "Form Recognizer") → Click **Create**
3. Fill in:
   - **Subscription**: Lab subscription
   - **Resource group**: `rg-claimsphere-hack`
   - **Region**: `East US`
   - **Name**: `adi-claimsphere`
   - **Pricing tier**: `Free F0` (500 pages/month — sufficient for demo)
     - If F0 not available: use `Standard S0` (first 500 pages/month free)
4. Click **Review + Create** → **Create**

### Copy Credentials:
1. Go to the resource → Left sidebar → **"Keys and Endpoint"**
2. Copy:
   - **KEY 1** → `.env` as `AZURE_DOCUMENT_INTELLIGENCE_KEY`
   - **Endpoint** → `.env` as `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`

---

## STEP 4 — AZURE AI SEARCH (Free Tier)

1. Click **"Create a resource"**
2. Search **"Azure AI Search"** (also shows as "Cognitive Search") → Click **Create**
3. Fill in:
   - **Subscription**: Lab subscription
   - **Resource group**: `rg-claimsphere-hack`
   - **Service name**: `srch-claimsphere` (globally unique — add suffix if taken)
   - **Location**: `East US`
   - **Pricing tier**: Click **"Change Pricing Tier"** → Select **FREE** (F) ← Very important!
4. Click **Review + Create** → **Create** (takes ~2 minutes)

### Create the Index:
1. Go to the new Search resource
2. Left sidebar → **"Indexes"** → Click **"+ Add index"**
3. **Index name**: `insurance-policies`
4. Add these fields:

| Field Name | Type | Retrievable | Searchable | Filterable |
|---|---|---|---|---|
| id | Edm.String | ✓ (Key) | | |
| policy_id | Edm.String | ✓ | ✓ | ✓ |
| policy_type | Edm.String | ✓ | ✓ | ✓ |
| holder_name | Edm.String | ✓ | ✓ | |
| sum_insured | Edm.Double | ✓ | | |
| coverage_details | Edm.String | ✓ | ✓ | |
| exclusions | Edm.String | ✓ | ✓ | |
| start_date | Edm.String | ✓ | | |
| end_date | Edm.String | ✓ | | |
| deductible | Edm.Double | ✓ | | |

5. Click **Save**

### Copy Credentials:
1. Left sidebar → **"Keys"**
2. Copy **Primary admin key** → `.env` as `AZURE_SEARCH_ADMIN_KEY`
3. Copy the **URL** from the Overview page → `.env` as `AZURE_SEARCH_ENDPOINT`
   - Format: `https://srch-claimsphere.search.windows.net`

---

## STEP 5 — AZURE STORAGE ACCOUNT

1. Click **"Create a resource"** → Search **"Storage account"** → **Create**
2. Fill in:
   - **Subscription**: Lab subscription
   - **Resource group**: `rg-claimsphere-hack`
   - **Storage account name**: `stclaimsphere` + 4 random chars (e.g., `stclaimsphereax42`)
     - Must be lowercase, 3-24 chars, globally unique
   - **Region**: `East US`
   - **Performance**: `Standard`
   - **Redundancy**: `Locally-redundant storage (LRS)` ← Cheapest!
3. Click **Review + Create** → **Create**

### Create Container:
1. Go to the storage account → Left sidebar → **"Containers"**
2. Click **"+ Container"**
3. Name: `claim-documents`
4. Public access level: `Private` ← Keep documents secure
5. Click **Create**

### Copy Credentials:
1. Left sidebar → **"Access keys"**
2. Click **"Show keys"**
3. Copy **Connection string** (under key1) → `.env` as `AZURE_STORAGE_CONNECTION_STRING`

---

## STEP 6 — AZURE KEY VAULT (Secrets Management)

1. Click **"Create a resource"** → Search **"Key vault"** → **Create**
2. Fill in:
   - **Subscription**: Lab subscription
   - **Resource group**: `rg-claimsphere-hack`
   - **Key vault name**: `kv-claimsphere` (globally unique)
   - **Region**: `East US`
   - **Pricing tier**: `Standard`
3. Click **Review + Create** → **Create**

### Add Secrets:
1. Go to Key Vault → Left sidebar → **"Secrets"**
2. Click **"+ Generate/Import"** for each secret:
   - `openai-api-key` = your OpenAI KEY 1
   - `doc-intelligence-key` = your Doc Intelligence KEY 1
   - `search-admin-key` = your Search admin key
   - `storage-connection-string` = your Storage connection string

---

## STEP 7 — AZURE FUNCTIONS APP (Backend Hosting)

1. Click **"Create a resource"** → Search **"Function App"** → **Create**
2. Fill in:
   - **Subscription**: Lab subscription
   - **Resource group**: `rg-claimsphere-hack`
   - **Function App name**: `func-claimsphere` (globally unique)
   - **Do you want to deploy code or container image?**: `Code`
   - **Runtime stack**: `Python`
   - **Version**: `3.11`
   - **Region**: `East US`
   - **Operating System**: `Linux`
   - **Hosting**: `Consumption (Serverless)` ← Cheapest — NOT Premium!
3. Click **Next: Storage** → Select your existing storage account `stclaimsphere...`
4. Click **Next: Monitoring** → Enable Application Insights: `Yes`
5. Click **Review + Create** → **Create** (takes ~3 minutes)

### Add Application Settings (Environment Variables):
1. Go to Function App → Left sidebar → **"Configuration"** → **"Application settings"**
2. Click **"+ New application setting"** for each variable from your `.env`:

```
DEMO_MODE                              = false
AZURE_OPENAI_ENDPOINT                  = https://oai-claimsphere.openai.azure.com/
AZURE_OPENAI_API_KEY                   = <your key>
AZURE_OPENAI_API_VERSION               = 2024-02-01
AZURE_OPENAI_GPT4O_MINI_DEPLOYMENT     = gpt-4o-mini
AZURE_OPENAI_GPT4O_DEPLOYMENT          = gpt-4o
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT   = <your endpoint>
AZURE_DOCUMENT_INTELLIGENCE_KEY        = <your key>
AZURE_SEARCH_ENDPOINT                  = https://srch-claimsphere.search.windows.net
AZURE_SEARCH_ADMIN_KEY                 = <your key>
AZURE_SEARCH_INDEX_NAME                = insurance-policies
AZURE_STORAGE_CONNECTION_STRING        = <your connection string>
AZURE_STORAGE_CONTAINER_NAME           = claim-documents
```

3. Click **Save** at the top

### Deploy the Code:
Option A — GitHub Actions (recommended):
1. In Function App → Left sidebar → **"Deployment Center"**
2. Source: **GitHub**
3. Authorize GitHub → Select your repo → Select branch `main`
4. Click **Save** — Azure will auto-deploy on every push

Option B — VS Code Extension:
1. Install **Azure Functions** extension in VS Code
2. Open the project folder
3. Click the Azure icon → Functions → Deploy to Function App
4. Select `func-claimsphere`

Option C — Azure CLI (from terminal):
```bash
# Install Azure CLI first: https://aka.ms/installazurecliwindows
az login
az functionapp deployment source config-zip \
  --resource-group rg-claimsphere-hack \
  --name func-claimsphere \
  --src deploy.zip
```

---

## STEP 8 — POWER PLATFORM SETUP

### 8A. Access Power Platform
1. Go to: https://make.powerapps.com
2. Sign in with the SAME lab credentials from Azure portal
3. You should see a **Default** environment already created

### 8B. Create Dataverse Tables
1. In Power Apps → Left sidebar → **"Tables"**
2. Click **"+ New table"** → **"Add columns and data"**

**Create Table: cs_claim**
Click "New table", name it `Claim`, then add columns:

| Display Name | Column Name | Type |
|---|---|---|
| Claim Number | cs_claimnumber | Single line text |
| Claim Type | cs_claimtype | Choice (Health/Motor/Property/Travel) |
| Status | cs_status | Choice (Received/Processing/Pending Info/Under Review/Approved/Rejected/Escalated) |
| Claimant Name | cs_claimantname | Single line text |
| Claimant Email | cs_claimantemail | Email |
| Claim Amount | cs_claimamount | Currency |
| Approved Amount | cs_approvedamount | Currency |
| Final Payout | cs_finalpayout | Currency |
| Policy ID | cs_policyid | Single line text |
| Incident Date | cs_incidentdate | Date only |
| Decision | cs_decision | Choice (Approve/Reject/Escalate) |
| Fraud Score | cs_fraudscore | Whole number |
| Confidence Score | cs_confidencescore | Decimal number |
| Rationale | cs_rationale | Multiline text |
| STP Flag | cs_stpflag | Yes/No |
| Channel | cs_channel | Choice (Web/Email/Teams/Phone) |
| Description | cs_description | Multiline text |

3. Click **Save**

**Create Table: cs_claimdocument** (similar process)

| Display Name | Type |
|---|---|
| Claim ID (lookup) | Lookup → cs_claim |
| Document Type | Choice |
| Blob URL | URL |
| Extraction Confidence | Decimal |
| Is Valid | Yes/No |

**Create Table: cs_claimauditlog**

| Display Name | Type |
|---|---|
| Claim ID (lookup) | Lookup → cs_claim |
| Agent Name | Single line text |
| Action | Single line text |
| Details | Multiline text |

### 8C. Get Dataverse URL for .env
1. Power Apps → Settings (gear icon) → **Session details**
2. Copy the **Instance URL** (e.g., `https://orgxxxxxxx.crm.dynamics.com`)
3. Add to `.env` as `DATAVERSE_URL`

### 8D. Register App for Dataverse API Access
1. Go to: https://portal.azure.com
2. Search **"App registrations"** → **"+ New registration"**
3. Name: `claimsphere-api-app`
4. Account type: **Single tenant**
5. Click **Register**
6. Copy **Application (client) ID** → `.env` as `DATAVERSE_CLIENT_ID`
7. Copy **Directory (tenant) ID** → `.env` as `DATAVERSE_TENANT_ID`
8. Left sidebar → **"Certificates & secrets"** → **"+ New client secret"**
9. Description: `claimsphere-secret`, Expires: `6 months`
10. Copy the **Value** (shown only once!) → `.env` as `DATAVERSE_CLIENT_SECRET`
11. In Power Apps → Settings → **Admin center** → Environments → Your env
12. Settings → Users + Permissions → **Application users** → **+ New app user**
13. Add your app `claimsphere-api-app` → Assign **System Administrator** role

---

## STEP 9 — COPILOT STUDIO BOT SETUP

### 9A. Access Copilot Studio
1. Go to: https://copilotstudio.microsoft.com
2. Sign in with lab credentials
3. Click **"Create"** → **"New copilot"**

### 9B. Create Intake Copilot
1. Name: `ClaimSphere Intake Bot`
2. Description: `AI-powered insurance claim intake and status tracking`
3. Language: English
4. Click **Create**

### 9C. Configure Topics
In the Copilot Studio editor, create these topics:

**Topic 1: Submit New Claim**
- Trigger phrases: "I want to file a claim", "submit claim", "new claim", "make a claim"
- Questions to ask:
  1. "What type of insurance claim? (Health / Motor / Property)"
  2. "What is your Policy ID?"
  3. "What is the incident date?"
  4. "Briefly describe what happened"
  5. "What is the approximate claim amount in rupees?"
  6. "Please upload your supporting documents (you can add them later too)"
- Action: Call Power Automate flow "Submit Claim Flow"
- End message: "Your claim [Claim ID] has been registered! I'll process it and update you via email."

**Topic 2: Check Claim Status**
- Trigger phrases: "check status", "claim update", "what happened to my claim"
- Questions: "Please provide your Claim ID"
- Action: Call HTTP Action → GET /claims/{claim_id}/status
- Display: Status, Decision, Payout amount

**Topic 3: Policy Q&A**
- Trigger phrases: "what does my policy cover", "am I covered for", "policy terms"
- Action: Call Power Automate → Support Agent API
- Display AI response

### 9D. Connect to Teams and Web
1. In Copilot Studio → **"Channels"** (left sidebar)
2. Click **"Microsoft Teams"** → **"Add to Teams"** → Follow instructions
3. Click **"Demo website"** → Copy the embed code for web deployment

---

## STEP 10 — POWER AUTOMATE FLOWS

### Flow 1: Claim Submission Flow
1. Go to: https://make.powerautomate.com
2. **"+ Create"** → **"Automated cloud flow"**
3. Trigger: **"When a HTTP request is received"** (manual trigger from Copilot Studio)
4. Actions:
   - **HTTP** action → POST to `https://func-claimsphere.azurewebsites.net/api/claims/submit`
   - **Create row** → Dataverse → cs_claim table (save initial record)
   - **Send email (V2)** → Send confirmation to claimant
5. Save and copy the HTTP POST URL → Configure in Copilot Studio

### Flow 2: Human-in-Loop Escalation Flow
1. **"+ Create"** → **"Automated cloud flow"**
2. Trigger: **"When a row is added, modified or deleted"** → Dataverse cs_claim
3. Condition: `Status equals "Under Human Review"`
4. True branch:
   - **Post adaptive card and wait for a response** (Teams connector)
   - Team: Claims Team
   - Card: (see Adaptive Card template below)
5. After response:
   - **Update row** → Dataverse → cs_claim → Decision = response
   - **HTTP** POST → `/claims/{claim_id}/human-decision`
   - **Send email** to claimant

### Adaptive Card Template for Teams:
```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.3",
  "body": [
    {
      "type": "TextBlock",
      "text": "🔔 Claim Requires Human Review",
      "weight": "Bolder",
      "size": "Large",
      "color": "Warning"
    },
    {
      "type": "FactSet",
      "facts": [
        {"title": "Claim ID:", "value": "${claim_id}"},
        {"title": "Type:", "value": "${claim_type}"},
        {"title": "Amount:", "value": "₹${claim_amount}"},
        {"title": "Claimant:", "value": "${claimant_name}"},
        {"title": "Fraud Score:", "value": "${fraud_score}/100"},
        {"title": "Escalation Reason:", "value": "${escalation_reason}"}
      ]
    },
    {
      "type": "TextBlock",
      "text": "AI Recommendation:",
      "weight": "Bolder"
    },
    {
      "type": "TextBlock",
      "text": "${ai_rationale}",
      "wrap": true
    }
  ],
  "actions": [
    {
      "type": "Action.Submit",
      "title": "✅ Approve",
      "style": "positive",
      "data": {"decision": "Approve", "claim_id": "${claim_id}"}
    },
    {
      "type": "Action.Submit",
      "title": "❌ Reject",
      "style": "destructive",
      "data": {"decision": "Reject", "claim_id": "${claim_id}"}
    },
    {
      "type": "Action.Submit",
      "title": "📋 Request More Info",
      "data": {"decision": "MoreInfo", "claim_id": "${claim_id}"}
    }
  ]
}
```

---

## STEP 11 — POWER BI DASHBOARD

1. Go to: https://app.powerbi.com
2. **"Get data"** → **"Dataverse"**
3. Connect to your Power Platform environment
4. Select tables: `cs_claim`, `cs_claimauditlog`
5. Load data

### Create these visuals:
- **Card**: Total Claims (COUNT of cs_claim)
- **Card**: Approved Claims (COUNTIF status = Approved)
- **Card**: STP Rate % (stp_flag = true / total)
- **Card**: Average Fraud Score
- **Donut Chart**: Claims by Type (Health / Motor / Property)
- **Bar Chart**: Claims by Status
- **Line Chart**: Claims over time (daily)
- **Table**: Recent claims with ID, Amount, Decision, Payout
- **Gauge**: Average TAT (hours from submission to decision)

6. Save and publish to workspace

---

## STEP 12 — UPDATE YOUR .env FILE

After completing all steps above, your `.env` should look like:

```env
DEMO_MODE=false

AZURE_OPENAI_ENDPOINT=https://oai-claimsphere.openai.azure.com/
AZURE_OPENAI_API_KEY=abc123...your-key...xyz
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_GPT4O_MINI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_GPT4O_DEPLOYMENT=gpt-4o

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://adi-claimsphere.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=def456...

AZURE_SEARCH_ENDPOINT=https://srch-claimsphere.search.windows.net
AZURE_SEARCH_ADMIN_KEY=ghi789...
AZURE_SEARCH_INDEX_NAME=insurance-policies

AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=stclaimsphere...
AZURE_STORAGE_CONTAINER_NAME=claim-documents

DATAVERSE_URL=https://orgxxxxxxxx.crm.dynamics.com
DATAVERSE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DATAVERSE_CLIENT_SECRET=your~secret~value
DATAVERSE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## STEP 13 — RUN LOCALLY (TEST FIRST)

```bash
# Navigate to project folder
cd "E:\Nexora Project\hackathon-insurance-claim"

# Install dependencies
pip install -r requirements.txt

# Test with demo mode first (no Azure needed)
echo "DEMO_MODE=true" > .env
uvicorn backend.main:app --reload --port 8000

# Open browser: http://localhost:8000/docs
# Try: POST /claims/submit/sync with sample data

# Once Azure is configured, switch off demo mode
# Edit .env: DEMO_MODE=false
```

---

## STEP 14 — SEED POLICY DATA TO AZURE AI SEARCH

Run this once after Azure Search is configured:

```bash
python -c "
import asyncio
from backend.tools.ai_search import AISearchClient
from backend.tools.ai_search import DEMO_POLICIES

async def seed():
    client = AISearchClient()
    policies = list(DEMO_POLICIES.values())
    for i, p in enumerate(policies):
        p['id'] = p['policy_id']  # AI Search requires 'id' field
        await client.index_policy(p)
    print(f'Seeded {len(policies)} policies')

asyncio.run(seed())
"
```

---

## STEP 15 — RUN STREAMLIT DEMO UI

```bash
# In the project folder (separate terminal from the API)
streamlit run streamlit_app.py

# Opens at: http://localhost:8501
# This is the visual demo for judges
```

---

## VERIFICATION CHECKLIST

After setup, verify each service:

| Service | Test | Expected Result |
|---|---|---|
| FastAPI | GET http://localhost:8000/health | `{"status": "healthy"}` |
| OpenAI | POST /claims/submit/sync (with demo claim) | Decision returned |
| Doc Intelligence | Upload a PDF via /documents/upload | Extracted fields returned |
| AI Search | GET /mock/policies | 4 sample policies |
| Blob Storage | Upload doc → check Azure portal container | File appears |
| Dataverse | POST claim → check Power Apps Tables | Row created |
| Teams Bot | Message Copilot Studio bot in Teams | Bot responds |
| Power Automate | Trigger escalation → check Teams | Adaptive card appears |

---

## TROUBLESHOOTING

| Problem | Solution |
|---|---|
| OpenAI 401 Unauthorized | Wrong API key or endpoint. Re-copy from portal. |
| OpenAI 429 Too Many Requests | TPM cap hit. Wait 60s or increase cap in AI Foundry |
| Doc Intelligence 404 | Wrong endpoint format. Must end with `.cognitiveservices.azure.com/` |
| AI Search 403 | Wrong key type. Use Admin key, not Query key |
| Blob Storage AuthFailure | Connection string has extra spaces. Re-copy carefully |
| Dataverse 401 | App user not created or wrong tenant ID |
| Functions 500 | Check Application Insights logs. Add DEMO_MODE=true to test |

---

## COST MONITORING

1. Azure Portal → Search **"Cost Management + Billing"**
2. Select your subscription
3. Left sidebar → **"Cost analysis"**
4. Check daily spend — should be < $1/day for hackathon usage
5. You will receive email alerts at 25%, 50%, 75%, 85%, 90%, 95%, 100% of $55

**Daily spend targets:**
- Days 1-5 (setup + dev): < $0.50/day
- Days 6-10 (testing + demo): < $1.00/day
- Total for 10 days: < $8

If you see unexpected costs, check:
- Are any VMs or AKS clusters accidentally deployed? (Delete them)
- Is PTU model deployed? (Delete immediately, costs $2/hr)
- Is App Service plan Premium? (Downgrade to Consumption)
