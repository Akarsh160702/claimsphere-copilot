// Container Apps environment + the FastAPI backend container app.
// Runs in production mode (DEMO_MODE=false) with passwordless access to all
// Azure services via the user-assigned managed identity.
param location string
param tags object
param containerAppsEnvironmentName string
param containerAppName string
param logAnalyticsWorkspaceName string
param applicationInsightsConnectionString string

param userAssignedIdentityId string
param userAssignedIdentityClientId string
param containerRegistryLoginServer string

@description('Image to deploy. Defaults to a placeholder; azd replaces it with the built API image.')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param serviceName string = 'api'

// Service endpoints injected as env vars (consumed by backend/config.py)
param openAiEndpoint string
param gpt4oDeploymentName string
param gpt4oMiniDeploymentName string
param documentIntelligenceEndpoint string
param searchEndpoint string
param searchIndexName string = 'insurance-policies'
param storageBlobEndpoint string
param storageContainerName string
param keyVaultEndpoint string
param allowedCorsOrigin string = '*'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsWorkspaceName
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvironmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  // azd matches this tag to the "api" service in azure.yaml
  tags: union(tags, { 'azd-service-name': serviceName })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        corsPolicy: {
          allowedOrigins: [
            allowedCorsOrigin
          ]
          allowedMethods: [
            '*'
          ]
          allowedHeaders: [
            '*'
          ]
        }
      }
      registries: [
        {
          server: containerRegistryLoginServer
          identity: userAssignedIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            { name: 'DEMO_MODE', value: 'false' }
            { name: 'APP_ENV', value: 'production' }
            { name: 'AZURE_CLIENT_ID', value: userAssignedIdentityClientId }
            { name: 'AZURE_OPENAI_API_VERSION', value: '2024-02-01' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openAiEndpoint }
            { name: 'AZURE_OPENAI_GPT4O_DEPLOYMENT', value: gpt4oDeploymentName }
            { name: 'AZURE_OPENAI_GPT4O_MINI_DEPLOYMENT', value: gpt4oMiniDeploymentName }
            { name: 'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT', value: documentIntelligenceEndpoint }
            { name: 'AZURE_SEARCH_ENDPOINT', value: searchEndpoint }
            { name: 'AZURE_SEARCH_INDEX_NAME', value: searchIndexName }
            { name: 'AZURE_STORAGE_BLOB_ENDPOINT', value: storageBlobEndpoint }
            { name: 'AZURE_STORAGE_CONTAINER_NAME', value: storageContainerName }
            { name: 'AZURE_KEY_VAULT_ENDPOINT', value: keyVaultEndpoint }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: applicationInsightsConnectionString }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
}

output name string = containerApp.name
output uri string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output environmentName string = environment.name
