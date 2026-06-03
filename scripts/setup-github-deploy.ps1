# =============================================================================
# ClaimSphere — One-shot setup: OIDC service principal + GitHub secrets
# Run from the project root:  .\scripts\setup-github-deploy.ps1
# Requirements: az CLI logged in, gh CLI logged in (both already confirmed)
# =============================================================================

$AppId          = "9f3545a6-7bbe-4af1-ab65-88dcdfe7e289"
$SubscriptionId = "43eac29a-8a3e-4102-a0a8-d9fe8490727d"
$TenantId       = "4a7f3035-3320-49c6-9f85-caa0b5a7befd"
$ResourceGroup  = "rg-claimsphere-prod"
$AcrName        = "crttm5hktbncovu"
$ContainerApp   = "ca-api-ttm5hktbncovu"
$GitHubRepo     = "Akarsh160702/claimsphere-copilot"
$Branch         = "master"

Write-Host "`n[1/5] Creating service principal..." -ForegroundColor Cyan
az ad sp create --id $AppId
# Ignore "already exists" error — that's fine

Write-Host "`n[2/5] Assigning Contributor on resource group..." -ForegroundColor Cyan
az role assignment create `
    --assignee $AppId `
    --role "Contributor" `
    --scope "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup"

Write-Host "`n[3/5] Assigning AcrPush on container registry..." -ForegroundColor Cyan
$AcrId = az acr show --name $AcrName --query id -o tsv
az role assignment create `
    --assignee $AppId `
    --role "AcrPush" `
    --scope $AcrId

Write-Host "`n[4/5] Adding OIDC federated credential for GitHub Actions..." -ForegroundColor Cyan
$FedParams = @"
{
  "name": "github-$Branch",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:$GitHubRepo:ref:refs/heads/$Branch",
  "audiences": ["api://AzureADTokenExchange"]
}
"@
$FedParams | Out-File -Encoding utf8 -FilePath "$env:TEMP\fed-cred.json"
az ad app federated-credential create --id $AppId --parameters "@$env:TEMP\fed-cred.json"

Write-Host "`n[5/5] Setting GitHub repo secrets and variables..." -ForegroundColor Cyan
gh secret set AZURE_CLIENT_ID        --repo $GitHubRepo --body $AppId
gh secret set AZURE_TENANT_ID        --repo $GitHubRepo --body $TenantId
gh secret set AZURE_SUBSCRIPTION_ID  --repo $GitHubRepo --body $SubscriptionId

gh variable set AZURE_RESOURCE_GROUP --repo $GitHubRepo --body $ResourceGroup
gh variable set ACR_NAME             --repo $GitHubRepo --body $AcrName
gh variable set CONTAINERAPP_NAME    --repo $GitHubRepo --body $ContainerApp

Write-Host "`n[Done] Setup complete." -ForegroundColor Green
Write-Host "Trigger the first deploy by pushing any backend change, or run:" -ForegroundColor Yellow
Write-Host "  gh workflow run 'Deploy backend (Container Apps)' --repo $GitHubRepo" -ForegroundColor Yellow
