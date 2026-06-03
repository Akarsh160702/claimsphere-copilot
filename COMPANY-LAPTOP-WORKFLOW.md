# ClaimSphere Copilot — Company-Laptop & Deployment Workflow

> Read this first if you are moving the project from your personal laptop to your
> **locked-down company laptop** (no admin, no PowerShell, npm/pip/docker blocked,
> only VS Code + GitHub Copilot + a browser + git work).

---

## 1. The mental model (read this once)

**Your company laptop is a _thin editing client_. Nothing builds or runs on it.**

| Step | Where it happens | Tool used |
|---|---|---|
| Edit code | Company laptop | VS Code + **Copilot** |
| Move code between machines | Cloud | **git push / pull** (GitHub) |
| Build the React app | Cloud | **GitHub Actions** (Static Web Apps) |
| Build the Docker image | Cloud | **Azure Container Registry** build (via Actions) |
| Deploy to Azure | Cloud | **GitHub Actions** (triggered by push) |
| Run `az` commands | Browser | **Azure Cloud Shell** (portal.azure.com) |
| Actually run/build locally (optional) | Cloud | **GitHub Codespaces** (browser) |

You never run `npm install`, `pip install`, `docker`, `az`, or PowerShell on the
company laptop. Every one of those happens on a cloud machine. That is the whole
point of the restructure.

```
 Personal laptop (Claude Code)            Company laptop (Copilot only)
 ┌───────────────────────────┐            ┌───────────────────────────┐
 │ full dev + test locally   │            │ edit with Copilot         │
 │ git push  ───────────────────► GitHub ◄──────────────  git pull / push │
 └───────────────────────────┘     │      └───────────────────────────┘
                                    │ push to main triggers:
                                    ▼
                         ┌──────────────────────┐
                         │   GitHub Actions     │  (cloud build, no laptop)
                         └──────────┬───────────┘
                                    ▼
                   ┌────────────────────────────────┐
                   │  Company Azure subscription     │
                   │  • Container Apps  (backend)    │
                   │  • Static Web Apps (frontend)   │
                   └────────────────────────────────┘
```

---

## 2. One-time setup (do this once, mostly from a browser)

You can do **all** of this from the company laptop using only the browser and git.

### 2.1 Push the code to GitHub (from your personal laptop — easiest)

```bash
cd "E:\Nexora Project\hackathon-insurance-claim"
git init                       # already done if you see a .git folder
git add .
git commit -m "ClaimSphere Copilot"
git branch -M main
git remote add origin https://github.com/<you>/claimsphere-copilot.git
git push -u origin main
```

Make the repo **private**. On the company laptop you later just:
`git clone https://github.com/<you>/claimsphere-copilot.git`

### 2.2 Provision Azure resources — use **Azure Cloud Shell** (browser)

You have no local `az`. Use the browser instead: open
**https://portal.azure.com → click the `>_` Cloud Shell icon** (top bar). That is a
full `az` + `azd` terminal running in Azure, no install needed.

Two options:

**Option A — one command (recommended).** This repo already has `azure.yaml` +
Bicep in `infra/`, so `azd` provisions everything (Container App, ACR, Static Web
App, OpenAI, Search, Storage, Key Vault) in one go:

```bash
# In Azure Cloud Shell:
git clone https://github.com/<you>/claimsphere-copilot.git
cd claimsphere-copilot
azd auth login
azd up        # pick your company subscription + region (East US for gpt-4o)
```

**Option B — click through the portal** using `DEPLOYMENT.md` (Steps 1–12). Slower
but fully UI-driven. Use this if `azd up` is blocked by a company policy.

### 2.3 Create the deploy credentials (so GitHub can deploy to Azure)

Still in **Cloud Shell**, create a service principal with OIDC (no passwords stored):

```bash
# Fill in your values:
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
RG=rg-claimsphere-hack
APP_NAME=claimsphere-github-deploy

# Create the app + service principal scoped to your resource group
az ad app create --display-name "$APP_NAME"
APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)
az ad sp create --id "$APP_ID"
az role assignment create --assignee "$APP_ID" --role Contributor \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RG"

# Federate it to your GitHub repo's main branch (OIDC, no secret to leak)
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name":"github-main",
  "issuer":"https://token.actions.githubusercontent.com",
  "subject":"repo:<you>/claimsphere-copilot:ref:refs/heads/main",
  "audiences":["api://AzureADTokenExchange"]
}'

echo "AZURE_CLIENT_ID=$APP_ID"
echo "AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)"
echo "AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID"
```

### 2.4 Add GitHub secrets & variables (browser)

GitHub repo → **Settings → Secrets and variables → Actions**:

**Secrets:**
- `AZURE_CLIENT_ID` — from 2.3
- `AZURE_TENANT_ID` — from 2.3
- `AZURE_SUBSCRIPTION_ID` — from 2.3
- `AZURE_STATIC_WEB_APPS_API_TOKEN` — Portal → your Static Web App → **Manage
  deployment token** → copy

**Variables:**
- `AZURE_RESOURCE_GROUP` — e.g. `rg-claimsphere-hack`
- `ACR_NAME` — your Container Registry name (no `.azurecr.io`)
- `CONTAINERAPP_NAME` — e.g. `ca-claimsphere-api`

### 2.5 Configure backend app settings (one time, persists)

Portal → your **Container App → Settings → Containers → Environment variables**
(or Key Vault references). Add the same keys as `.env.example`
(`AZURE_OPENAI_API_KEY`, etc.). These persist across deploys, so the GitHub
workflow does **not** need to know your secrets.

---

## 3. Daily workflow on the company laptop

### Path A — edit & ship (the normal case)
1. `git pull` (VS Code Source Control panel, or terminal).
2. Edit code. Ask **Copilot Chat** for help (it replaces Claude Code here — see §5).
3. Commit + push to `main`.
4. GitHub Actions builds and deploys automatically. Watch progress in the repo's
   **Actions** tab. Done — no local build.

### Path B — run / build / debug for real (when editing isn't enough)
Open a **Codespace**: GitHub repo → green **Code** button → **Codespaces** →
**Create codespace on main**. After ~2 min you get a browser VS Code with a real
terminal:
```bash
uvicorn backend.main:app --reload --port 8000   # backend
cd frontend && npm run dev                        # frontend (new terminal)
```
Ports are forwarded with clickable preview URLs. `.devcontainer/devcontainer.json`
already installed everything. Copilot works inside the Codespace too.

### Path C — run an Azure command
Open **Cloud Shell** in the portal (browser). Never needs local `az`.

---

## 4. What works / what doesn't on the locked laptop

| Need | Blocked locally? | Do this instead |
|---|---|---|
| Edit code | ✅ works (VS Code) | — |
| AI pair-programming | Claude Code blocked | **GitHub Copilot** (§5) |
| Move code | ✅ git works | `git pull` / `git push` |
| Build React | npm blocked | GitHub Actions (auto) or Codespaces |
| Build backend image | docker blocked | ACR build via Actions (auto) |
| Run the app | python/node blocked | **Codespaces** (browser) |
| Provision/inspect Azure | az/PowerShell blocked | **Cloud Shell** (browser) |
| Install anything | no admin | nothing to install — all cloud |

---

## 5. Using Copilot where you used Claude Code

Claude Code won't run on the company laptop, but **Copilot Chat** in VS Code covers
day-to-day work. To keep it effective:
- This repo is heavily commented and has `CLAUDE.md` + this file — Copilot reads open
  files and the workspace for context, so keep relevant files open.
- Ask scoped questions: *"In `backend/orchestrator.py`, add a retry around the
  adjudication call"* rather than broad multi-file refactors.
- Use **Copilot Edits** (multi-file) for changes spanning a few files.
- For anything large/architectural, do it on your **personal laptop with Claude
  Code**, push, then pull on the company laptop.

---

## 6. Quick reference — first day on the company laptop

```text
1. Clone:        git clone https://github.com/<you>/claimsphere-copilot.git
2. Open in VS Code, sign into Copilot.
3. Need to run it?      -> open a Codespace (browser).
4. Need an Azure task?  -> open Cloud Shell (browser).
5. Ship a change?       -> commit + push to main -> Actions deploys it.
```
You never need admin, PowerShell, or a local toolchain. Ever.
