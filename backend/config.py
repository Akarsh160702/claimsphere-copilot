from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Demo mode — uses mock data, no Azure credentials needed
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")

    # Azure OpenAI
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(default="2024-02-01", alias="AZURE_OPENAI_API_VERSION")
    gpt4o_mini_deployment: str = Field(default="gpt-4o-mini", alias="AZURE_OPENAI_GPT4O_MINI_DEPLOYMENT")
    gpt4o_deployment: str = Field(default="gpt-4o", alias="AZURE_OPENAI_GPT4O_DEPLOYMENT")

    # Azure Document Intelligence
    doc_intelligence_endpoint: str = Field(default="", alias="AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    doc_intelligence_key: str = Field(default="", alias="AZURE_DOCUMENT_INTELLIGENCE_KEY")

    # Azure AI Search
    search_endpoint: str = Field(default="", alias="AZURE_SEARCH_ENDPOINT")
    search_admin_key: str = Field(default="", alias="AZURE_SEARCH_ADMIN_KEY")
    search_index_name: str = Field(default="insurance-policies", alias="AZURE_SEARCH_INDEX_NAME")

    # Azure Blob Storage
    storage_connection_string: str = Field(default="", alias="AZURE_STORAGE_CONNECTION_STRING")
    storage_blob_endpoint: str = Field(default="", alias="AZURE_STORAGE_BLOB_ENDPOINT")
    storage_container_name: str = Field(default="claim-documents", alias="AZURE_STORAGE_CONTAINER_NAME")

    # Managed identity (passwordless auth via DefaultAzureCredential in Azure).
    # When set, identifies which user-assigned identity to use.
    azure_client_id: str = Field(default="", alias="AZURE_CLIENT_ID")
    key_vault_endpoint: str = Field(default="", alias="AZURE_KEY_VAULT_ENDPOINT")

    # Dataverse
    dataverse_url: str = Field(default="", alias="DATAVERSE_URL")
    dataverse_client_id: str = Field(default="", alias="DATAVERSE_CLIENT_ID")
    dataverse_client_secret: str = Field(default="", alias="DATAVERSE_CLIENT_SECRET")
    dataverse_tenant_id: str = Field(default="", alias="DATAVERSE_TENANT_ID")

    # Power Automate / Teams
    power_automate_webhook_url: str = Field(default="", alias="POWER_AUTOMATE_WEBHOOK_URL")
    # The public URL of this API — used to build the Teams card callback URLs
    api_base_url: str = Field(
        default="https://ca-api-u5aqvvvbt34hq.politecliff-7ae23c60.eastus.azurecontainerapps.io",
        alias="API_BASE_URL",
    )

    # App
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    secret_key: str = Field(default="dev-secret-key-change-in-prod", alias="SECRET_KEY")

    # Azure Application Insights
    applicationinsights_connection_string: str = Field(
        default="", alias="APPLICATIONINSIGHTS_CONNECTION_STRING"
    )

    # Adjudication thresholds (configurable)
    auto_approve_max_amount: float = 500000.0   # Auto-approve up to ₹5L
    fraud_escalation_threshold: int = 60         # Escalate if fraud score >= 60
    confidence_escalation_threshold: float = 0.75  # Escalate if confidence < 75%
    high_value_escalation_amount: float = 1000000.0  # Escalate if > ₹10L

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
