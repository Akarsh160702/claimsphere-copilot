// Azure AI Search for policy RAG. Free tier by default (50 MB index).
// Managed identity gets data-plane + control-plane roles for keyless access.
param location string
param tags object
param searchName string
param principalId string

@allowed([
  'free'
  'basic'
  'standard'
])
param sku string = 'free'

resource search 'Microsoft.Search/searchServices@2024-03-01-preview' = {
  name: searchName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    disableLocalAuth: false
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

// Search Index Data Contributor (read/write documents in indexes)
var indexDataContributorRoleId = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
resource indexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, principalId, indexDataContributorRoleId)
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', indexDataContributorRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

// Search Service Contributor (create/manage indexes)
var serviceContributorRoleId = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
resource serviceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, principalId, serviceContributorRoleId)
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', serviceContributorRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

output name string = search.name
output endpoint string = 'https://${search.name}.search.windows.net'
