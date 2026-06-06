// ClaimSphere Copilot — infrastructure entry point.
// Subscription-scoped: creates the resource group and all resources, wiring the
// backend container app to every Azure service via a passwordless managed identity.
//
// Deploy with the Azure Developer CLI:  azd up
targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the azd environment — used to derive resource names.')
param environmentName string

@minLength(1)
@description('Primary location for all resources (e.g. eastus). Use a region with gpt-4o.')
param location string

@description('Region for the Static Web App (limited region set).')
param staticWebAppLocation string = 'eastus2'

@description('gpt-4o deployment capacity (x1000 TPM).')
param gpt4oCapacity int = 10

@description('gpt-4o-mini deployment capacity (x1000 TPM).')
param gpt4oMiniCapacity int = 50

@description('Azure AI Search SKU.')
param searchSku string = 'free'

@description('Search index name for policy RAG.')
param searchIndexName string = 'insurance-policies'

var abbrs = loadJsonContent('abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = {
  'azd-env-name': environmentName
  project: 'claimsphere-copilot'
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
  }
}

module identity 'modules/identity.bicep' = {
  name: 'identity'
  scope: rg
  params: {
    location: location
    tags: tags
    identityName: '${abbrs.managedIdentityUserAssignedIdentities}${resourceToken}'
  }
}

module registry 'modules/registry.bicep' = {
  name: 'registry'
  scope: rg
  params: {
    location: location
    tags: tags
    registryName: '${abbrs.containerRegistryRegistries}${resourceToken}'
    principalId: identity.outputs.principalId
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    location: location
    tags: tags
    keyVaultName: '${abbrs.keyVaultVaults}${resourceToken}'
    principalId: identity.outputs.principalId
  }
}

module openAi 'modules/openai.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    location: location
    tags: tags
    accountName: '${abbrs.cognitiveServicesOpenAI}${resourceToken}'
    principalId: identity.outputs.principalId
    gpt4oCapacity: gpt4oCapacity
    gpt4oMiniCapacity: gpt4oMiniCapacity
  }
}

module documentIntelligence 'modules/documentintelligence.bicep' = {
  name: 'documentintelligence'
  scope: rg
  params: {
    location: location
    tags: tags
    accountName: '${abbrs.cognitiveServicesDocumentIntelligence}${resourceToken}'
    principalId: identity.outputs.principalId
  }
}

module search 'modules/search.bicep' = {
  name: 'search'
  scope: rg
  params: {
    location: location
    tags: tags
    searchName: '${abbrs.searchSearchServices}${resourceToken}'
    principalId: identity.outputs.principalId
    sku: searchSku
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    location: location
    tags: tags
    storageAccountName: '${abbrs.storageStorageAccounts}${resourceToken}'
    principalId: identity.outputs.principalId
  }
}

module containerApps 'modules/containerapps.bicep' = {
  name: 'containerapps'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppsEnvironmentName: '${abbrs.appManagedEnvironments}${resourceToken}'
    containerAppName: '${abbrs.appContainerApps}api-${resourceToken}'
    logAnalyticsWorkspaceName: monitoring.outputs.logAnalyticsWorkspaceName
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    userAssignedIdentityId: identity.outputs.id
    userAssignedIdentityClientId: identity.outputs.clientId
    containerRegistryLoginServer: registry.outputs.loginServer
    openAiEndpoint: openAi.outputs.endpoint
    gpt4oDeploymentName: openAi.outputs.gpt4oDeploymentName
    gpt4oMiniDeploymentName: openAi.outputs.gpt4oMiniDeploymentName
    documentIntelligenceEndpoint: documentIntelligence.outputs.endpoint
    searchEndpoint: search.outputs.endpoint
    searchIndexName: searchIndexName
    storageBlobEndpoint: storage.outputs.blobEndpoint
    storageContainerName: storage.outputs.containerName
    keyVaultEndpoint: keyVault.outputs.endpoint
  }
}

module staticWebApp 'modules/staticwebapp.bicep' = {
  name: 'staticwebapp'
  scope: rg
  params: {
    location: staticWebAppLocation
    tags: tags
    name: '${abbrs.webStaticSites}${resourceToken}'
  }
}

// ── Outputs (azd writes these to .azure/<env>/.env) ──────────────────────────
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = subscription().tenantId
output RESOURCE_GROUP string = rg.name

output AZURE_CLIENT_ID string = identity.outputs.clientId

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = registry.outputs.name

output AZURE_OPENAI_ENDPOINT string = openAi.outputs.endpoint
output AZURE_OPENAI_GPT4O_DEPLOYMENT string = openAi.outputs.gpt4oDeploymentName
output AZURE_OPENAI_GPT4O_MINI_DEPLOYMENT string = openAi.outputs.gpt4oMiniDeploymentName

output AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT string = documentIntelligence.outputs.endpoint

output AZURE_SEARCH_ENDPOINT string = search.outputs.endpoint
output AZURE_SEARCH_INDEX_NAME string = searchIndexName

output AZURE_STORAGE_BLOB_ENDPOINT string = storage.outputs.blobEndpoint
output AZURE_STORAGE_CONTAINER_NAME string = storage.outputs.containerName

output AZURE_KEY_VAULT_ENDPOINT string = keyVault.outputs.endpoint

output AZURE_CONTAINER_APP_NAME string = containerApps.outputs.name
output SERVICE_API_URI string = containerApps.outputs.uri
output SERVICE_WEB_URI string = staticWebApp.outputs.uri
