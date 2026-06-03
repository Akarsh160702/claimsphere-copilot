// Azure Static Web App for the React/Vite frontend (Free tier, global CDN).
// Note: Static Web Apps are only available in a subset of regions, so this
// takes its own location parameter (default eastus2).
param location string
param tags object
param name string
param serviceName string = 'web'

resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: name
  location: location
  // azd matches this tag to the "web" service in azure.yaml
  tags: union(tags, { 'azd-service-name': serviceName })
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    provider: 'Custom'
    enterpriseGradeCdnStatus: 'Disabled'
  }
}

output name string = staticWebApp.name
output uri string = 'https://${staticWebApp.properties.defaultHostname}'
