# ClaimSphere Copilot — Infrastructure (Bicep + azd)

One-command provisioning and deployment of the whole stack to Azure using the
**Azure Developer CLI (`azd`)** and **Bicep**.

## What gets created

All in a single resource group (`rg-<env-name>`), wired together with a
**user-assigned managed identity** (passwordless — no keys in code):

| Resource | Purpose |
|---|---|
| Log Analytics + Application Insights | Observability / telemetry |
| User-assigned Managed Identity | Passwordless auth for the backend |
| Azure Container Registry (Basic) | Holds the built API image |
| Key Vault (RBAC) | Secrets store |
| Azure OpenAI (S0) + `gpt-4o` + `gpt-4o-mini` | Agent reasoning + adjudication |
| Azure AI Document Intelligence (S0) | OCR / extraction |
| Azure AI Search (Free) | Policy RAG |
| Storage Account + `claim-documents` container | Document storage |
| Container Apps env + **API** container app | FastAPI backend (`DEMO_MODE=false`) |
| Static Web App (Free) | React/Vite frontend |

The managed identity is granted least-privilege data-plane roles on each service
(OpenAI User, Cognitive Services User, Search Index Data Contributor + Service
Contributor, Storage Blob Data Contributor, Key Vault Secrets User, AcrPull).

## Prerequisites

1. **Azure Developer CLI** (bundles Bicep): https://aka.ms/install-azd
   - Windows: `winget install microsoft.azd`
2. **Azure CLI**: https://aka.ms/installazd → `winget install -e --id Microsoft.AzureCLI`
3. **Docker Desktop** running (azd builds the API image locally).
4. An Azure subscription with quota for **gpt-4o** and **gpt-4o-mini** in your
   chosen region (e.g. `eastus`). Check in the Azure AI Foundry portal first.

## Deploy

From the **repo root** (`hackathon-insurance-claim/`):

```bash
azd auth login
azd up
```

`azd up` will prompt for:
- **Environment name** (e.g. `claimsphere-dev`) → becomes `rg-claimsphere-dev`
- **Azure subscription**
- **Location** (pick a gpt-4o region such as `East US`)

It then provisions everything (`infra/main.bicep`), builds & pushes the API
image, deploys the container app, builds the frontend and deploys it to the
Static Web App. Outputs (endpoints, URLs) are written to `.azure/<env>/.env`.

### Useful follow-ups

```bash
azd provision     # infra only
azd deploy        # app code only (skip infra)
azd deploy api    # just the backend
azd deploy web    # just the frontend
azd down          # delete everything (stops the billing clock)
azd env get-values
```

### Tuning (optional)

```bash
azd env set AZURE_OPENAI_GPT4O_CAPACITY 10        # x1000 TPM
azd env set AZURE_OPENAI_GPT4O_MINI_CAPACITY 50
azd env set AZURE_SEARCH_SKU basic                 # if Free quota is exhausted
azd env set AZURE_STATIC_WEB_APP_LOCATION eastus2  # SWA supported region
```
(These map to the defaulted parameters in `main.bicep`.)

## Connecting the frontend to the deployed API

After `azd up`, set the frontend's backend origin to the container app URL and
redeploy the web service:

```bash
azd env set VITE_BACKEND_ORIGIN <SERVICE_API_URI from azd output>
azd deploy web
```

## Important: passwordless storage requires the identity refactor

The container app runs with `DEMO_MODE=false` and authenticates to OpenAI,
Document Intelligence and AI Search via the managed identity automatically once
the SDK clients use `DefaultAzureCredential`. **Blob Storage** currently uses a
connection string in `backend/tools/blob_storage.py`; switching it to
`BlobServiceClient(AZURE_STORAGE_BLOB_ENDPOINT, credential=DefaultAzureCredential())`
is the next step (the config field `storage_blob_endpoint` is already wired). The
infra grants the identity **Storage Blob Data Contributor** so it's ready.

## Cost

Built to stay near the **$55** hackathon budget: Search Free, Storage LRS, ACR
Basic, Container Apps scale-to-low, OpenAI **Standard (pay-as-you-go, never
PTU)**. Run `azd down` when not demoing. Estimated idle footprint is a few
dollars; OpenAI is metered per token.

## Files

```
azure.yaml                 azd manifest (api + web services)
Dockerfile                 backend image (repo root)
infra/
  main.bicep               subscription-scoped entry point
  main.parameters.json     azd parameter bindings
  abbreviations.json       resource naming prefixes
  modules/
    monitoring.bicep       Log Analytics + App Insights
    identity.bicep         user-assigned managed identity
    registry.bicep         Azure Container Registry (+ AcrPull)
    keyvault.bicep         Key Vault (+ Secrets User)
    openai.bicep           OpenAI + gpt-4o / gpt-4o-mini (+ OpenAI User)
    documentintelligence.bicep
    search.bicep           AI Search (+ data/service roles)
    storage.bicep          Storage + container (+ Blob Data Contributor)
    containerapps.bicep    Container Apps env + API app
    staticwebapp.bicep     Static Web App (frontend)
```
