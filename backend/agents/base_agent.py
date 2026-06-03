from abc import ABC, abstractmethod
from openai import AsyncAzureOpenAI
import structlog

from backend.config import get_settings
from backend.models.claim import ClaimContext

logger = structlog.get_logger()


def get_openai_client() -> AsyncAzureOpenAI:
    settings = get_settings()
    if settings.azure_openai_api_key:
        return AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
    # Managed identity path (Container Apps in production — no API key stored)
    from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    return AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=settings.azure_openai_api_version,
    )


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.settings = get_settings()
        self._client: AsyncAzureOpenAI = None

    @property
    def client(self) -> AsyncAzureOpenAI:
        if self._client is None:
            self._client = get_openai_client()
        return self._client

    @abstractmethod
    async def process(self, context: ClaimContext) -> ClaimContext:
        pass

    async def call_llm(
        self,
        messages: list[dict],
        model: str = None,
        response_format: dict = None,
        temperature: float = 0.1,
    ) -> str:
        if model is None:
            model = self.settings.gpt4o_mini_deployment

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def log(self, event: str, **kwargs):
        logger.info(event, agent=self.name, **kwargs)

    def log_error(self, event: str, **kwargs):
        logger.error(event, agent=self.name, **kwargs)
