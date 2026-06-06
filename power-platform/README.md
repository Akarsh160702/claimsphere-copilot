# Power Platform Integration — ClaimSphere Copilot

This directory contains the Microsoft Power Platform integration assets for ClaimSphere.

## Architecture

```
ClaimSphere Backend (FastAPI on Azure Container Apps)
    │
    ├─► Power Automate HTTP Trigger  ──► Teams Adaptive Card (escalation alert)
    │        (POWER_AUTOMATE_WEBHOOK_URL)       │
    │                                           ▼
    │                               Adjudicator clicks button
    │                                           │
    ◄─── POST /webhooks/teams-decision ◄────────┘
         (decision applied in real time)
    │
    └─► Copilot Studio Bot ──► /support/query (RAG)
                            └─► /claims/{id}/status
```

## Files

| File | Purpose |
|------|---------|
| `teams-adaptive-card.json` | Adaptive Card template — reference design for the escalation notification |
| `flow-escalation-template.json` | Step-by-step guide + schema to build the Power Automate flow |
| `copilot-studio-skill.yaml` | Copilot Studio action definitions — connects bot to backend API |

## Setup — Power Automate Escalation Flow (30 minutes)

### Step 1 — Create the flow

1. Go to [make.powerautomate.com](https://make.powerautomate.com)
2. **New flow → Instant cloud flow → Skip**
3. Add trigger: **When an HTTP request is received**
4. Paste the JSON schema from `flow-escalation-template.json` → trigger.schema
5. Click **Save** and copy the generated **HTTP POST URL**

### Step 2 — Wire to backend

Add the URL to your environment:

```bash
# GitHub secret (for CI/CD)
POWER_AUTOMATE_WEBHOOK_URL=https://prod-xx.eastus.logic.azure.com/workflows/...

# Or in Azure Container Apps environment variable
az containerapp env dotenv set ... POWER_AUTOMATE_WEBHOOK_URL=<url>
```

### Step 3 — Add Teams notification

Back in Power Automate:

1. Add action: **Parse JSON** → content: `@triggerBody()`, use the trigger schema
2. Add action: **Microsoft Teams → Post adaptive card in a chat or channel**
   - Team: your claims review team
   - Channel: `#claims-review`
   - Adaptive Card: `@{body('Parse_JSON')?['adaptive_card']}`
3. Add action: **Response** → Status: 202

### Step 4 — Test

Submit a claim with a high fraud score (≥60) or low confidence (< 75%) — the backend will escalate it and fire the webhook. You'll see the Adaptive Card appear in Teams with **Approve / Reject / Request More Info** buttons.

Clicking a button fires a POST back to `/webhooks/teams-decision` and the ClaimSphere UI updates in real time.

## Setup — Copilot Studio Bot (1 hour)

1. Go to [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com)
2. **Create → New copilot → blank**
3. Name: `ClaimSphere Assistant`
4. **Actions → Add action → Create new action → HTTP**
5. For each action in `copilot-studio-skill.yaml`:
   - Set method, endpoint, and request schema
   - Map response fields using the response_mapping
6. Add trigger phrases from the YAML
7. Configure escalation → **Transfer to agent**
8. Publish to Teams channel

## Dataverse Tables (optional — enhances persistence)

| Table | Purpose |
|-------|---------|
| `cs_claims` | Claim records (already wired in DataverseClient) |
| `cs_claimdocuments` | Document metadata |
| `cs_claimauditlogs` | Full agent audit trail |

Configure by setting the `DATAVERSE_*` variables in your environment.
The `DataverseClient` in `backend/tools/dataverse.py` uses OData v4 and
falls back to in-memory storage when credentials are not set.
