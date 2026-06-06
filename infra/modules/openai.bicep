// Azure OpenAI account. Model deployments are created separately after quota is approved.
// New Azure free accounts have 0 quota by default — request via Azure portal.
param location string
param tags object
param accountName string
param principalId string
param gpt4oCapacity int = 10
param gpt4oMiniCapacity int = 10
param gpt4oModelVersion string = '2024-11-20'
param gpt4oMiniModelVersion string = '2024-07-18'
param deployModels bool = false  // set true after quota is approved

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

// gpt-4o-mini deployment — only created when deployModels=true (quota approved)
resource gpt4oMini 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (deployModels) {
  parent: account
  name: 'gpt-4o-mini'
  sku: {
    name: 'GlobalStandard'
    capacity: gpt4oMiniCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: gpt4oMiniModelVersion
    }
  }
}

// gpt-4o adjudication deployment — only created when deployModels=true
resource gpt4o 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (deployModels) {
  parent: account
  name: 'gpt-4o'
  dependsOn: [
    gpt4oMini
  ]
  sku: {
    name: 'GlobalStandard'
    capacity: gpt4oCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: gpt4oModelVersion
    }
  }
}

// Cognitive Services OpenAI User role for managed identity
var openAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
resource openAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(account.id, principalId, openAiUserRoleId)
  scope: account
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

output name string = account.name
output endpoint string = account.properties.endpoint
output gpt4oDeploymentName string = 'gpt-4o'
output gpt4oMiniDeploymentName string = 'gpt-4o-mini'
