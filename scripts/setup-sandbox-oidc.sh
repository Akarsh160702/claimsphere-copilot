#!/usr/bin/env bash
# =============================================================================
# ClaimSphere Copilot — Sandbox OIDC setup
#
# Run this ONCE from Azure Cloud Shell (bash) inside your company's tenant.
# It creates a service principal, wires it to GitHub Actions via OIDC, and
# assigns it Owner on your sandbox subscription so the Bicep can provision
# all resources (including role assignments for the managed identity).
#
# Usage:
#   bash scripts/setup-sandbox-oidc.sh \
#     --repo "Akarsh160702/claimsphere-copilot" \
#     --subscription "<SANDBOX_SUBSCRIPTION_ID>"
#
# Optional:
#   --branch "master"   (default: master — branch that triggers deploys)
# =============================================================================

set -euo pipefail

# ── Argument parsing ──────────────────────────────────────────────────────────
REPO=""
SUBSCRIPTION_ID=""
BRANCH="master"

usage() {
  echo "Usage: $0 --repo <owner/repo> --subscription <subscription-id> [--branch <branch>]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)         REPO="$2";            shift 2 ;;
    --subscription) SUBSCRIPTION_ID="$2"; shift 2 ;;
    --branch)       BRANCH="$2";          shift 2 ;;
    -h|--help)      usage ;;
    *)              echo "Unknown argument: $1"; usage ;;
  esac
done

[[ -z "$REPO" ]]            && { echo "ERROR: --repo is required";         usage; }
[[ -z "$SUBSCRIPTION_ID" ]] && { echo "ERROR: --subscription is required"; usage; }

APP_NAME="claimsphere-sandbox-gha"
GITHUB_ISSUER="https://token.actions.githubusercontent.com"

echo ""
echo "========================================================"
echo "  ClaimSphere — Sandbox OIDC service principal setup"
echo "  GitHub repo    : $REPO"
echo "  Subscription   : $SUBSCRIPTION_ID"
echo "  Branch trigger : $BRANCH"
echo "========================================================"
echo ""

# Point az at the sandbox subscription
az account set --subscription "$SUBSCRIPTION_ID"
TENANT_ID=$(az account show --query tenantId -o tsv)
echo "Tenant : $TENANT_ID"
echo ""

# ── Step 1: App Registration ─────────────────────────────────────────────────
echo "1/4  Creating App Registration '$APP_NAME'..."
# If it already exists, reuse it (idempotent)
EXISTING=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)
if [[ -n "$EXISTING" ]]; then
  APP_ID="$EXISTING"
  echo "     Reusing existing app: $APP_ID"
else
  APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
  echo "     Created: $APP_ID"
fi

# ── Step 2: Service Principal ─────────────────────────────────────────────────
echo "2/4  Ensuring Service Principal exists..."
SP_OID=$(az ad sp show --id "$APP_ID" --query id -o tsv 2>/dev/null || true)
if [[ -z "$SP_OID" ]]; then
  SP_OID=$(az ad sp create --id "$APP_ID" --query id -o tsv)
  echo "     Created SP: $SP_OID"
else
  echo "     Reusing SP: $SP_OID"
fi

# ── Step 3: OIDC Federated Credentials ───────────────────────────────────────
echo "3/4  Configuring OIDC federated credentials..."

add_credential() {
  local name="$1" subject="$2"
  # Skip if credential with this name already exists
  EXISTING_CRED=$(az ad app federated-credential list --id "$APP_ID" \
    --query "[?name=='$name'].name" -o tsv 2>/dev/null || true)
  if [[ -n "$EXISTING_CRED" ]]; then
    echo "     Credential '$name' already exists, skipping."
    return
  fi
  az ad app federated-credential create --id "$APP_ID" --parameters "{
    \"name\": \"$name\",
    \"issuer\": \"$GITHUB_ISSUER\",
    \"subject\": \"$subject\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }" > /dev/null
  echo "     Added credential: $name"
}

# Push to the main branch (triggers deploy-backend-sandbox + deploy-frontend-sandbox)
add_credential "github-branch-${BRANCH}" "repo:${REPO}:ref:refs/heads/${BRANCH}"

# GitHub Environment 'sandbox' — used by provision-sandbox.yml
add_credential "github-env-sandbox"     "repo:${REPO}:environment:sandbox"

# workflow_dispatch from any branch
add_credential "github-dispatch"        "repo:${REPO}:ref:refs/heads/${BRANCH}"

# ── Step 4: Role Assignment ───────────────────────────────────────────────────
echo "4/4  Assigning Owner on subscription $SUBSCRIPTION_ID..."
echo "     (Owner is required so Bicep can assign roles to the managed identity.)"
echo "     (If your IT policy disallows Owner, contact your subscription admin.)"

EXISTING_ROLE=$(az role assignment list \
  --assignee "$SP_OID" \
  --role "Owner" \
  --scope "/subscriptions/$SUBSCRIPTION_ID" \
  --query "[0].id" -o tsv 2>/dev/null || true)

if [[ -n "$EXISTING_ROLE" ]]; then
  echo "     Owner already assigned, skipping."
else
  az role assignment create \
    --role "Owner" \
    --assignee-object-id "$SP_OID" \
    --assignee-principal-type ServicePrincipal \
    --scope "/subscriptions/$SUBSCRIPTION_ID" \
    --output none
  echo "     Owner assigned."
fi

# ── Output ────────────────────────────────────────────────────────────────────
echo ""
echo "========================================================"
echo ""
echo "  DONE. Add these 3 values to your GitHub repo:"
echo ""
echo "  github.com/$REPO"
echo "  → Settings → Environments → Create 'sandbox' → Add Secrets"
echo ""
printf "  %-38s %s\n" "AZURE_SANDBOX_CLIENT_ID"        "$APP_ID"
printf "  %-38s %s\n" "AZURE_SANDBOX_TENANT_ID"        "$TENANT_ID"
printf "  %-38s %s\n" "AZURE_SANDBOX_SUBSCRIPTION_ID"  "$SUBSCRIPTION_ID"
echo ""
echo "  Then go to GitHub Actions and run:"
echo "  'Provision infra (sandbox)' workflow manually."
echo "========================================================"
