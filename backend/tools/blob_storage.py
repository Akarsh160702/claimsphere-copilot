import uuid
import asyncio
from typing import Optional
import structlog

from backend.config import get_settings

logger = structlog.get_logger()


class BlobStorageClient:
    def __init__(self):
        self.settings = get_settings()
        self._client = None

    def _get_client(self):
        if self._client is None and not self.settings.demo_mode:
            from azure.storage.blob import BlobServiceClient
            if self.settings.storage_connection_string:
                self._client = BlobServiceClient.from_connection_string(
                    self.settings.storage_connection_string
                )
            else:
                # Managed identity path (Container Apps — AZURE_STORAGE_BLOB_ENDPOINT set)
                from azure.identity import DefaultAzureCredential
                self._client = BlobServiceClient(
                    account_url=self.settings.storage_blob_endpoint,
                    credential=DefaultAzureCredential(),
                )
        return self._client

    async def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        claim_id: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        if self.settings.demo_mode:
            await asyncio.sleep(0.1)
            blob_name = f"{claim_id}/{uuid.uuid4()}-{filename}"
            return f"https://demo-storage.blob.core.windows.net/claim-documents/{blob_name}"

        try:
            client = self._get_client()
            container = client.get_container_client(self.settings.storage_container_name)
            blob_name = f"{claim_id}/{uuid.uuid4()}-{filename}"
            blob_client = container.get_blob_client(blob_name)
            from azure.storage.blob import ContentSettings
            blob_client.upload_blob(
                file_bytes,
                blob_type="BlockBlob",
                content_settings=ContentSettings(content_type=content_type),
                overwrite=True,
            )
            return blob_client.url
        except Exception as e:
            logger.error("blob_upload_failed", error=str(e), filename=filename)
            raise

    async def download_document(self, blob_url: str) -> Optional[bytes]:
        if self.settings.demo_mode:
            await asyncio.sleep(0.1)
            return b"demo-document-content"

        try:
            from azure.storage.blob import BlobClient
            if self.settings.storage_connection_string:
                blob_client = BlobClient.from_blob_url(blob_url)
            else:
                from azure.identity import DefaultAzureCredential
                blob_client = BlobClient.from_blob_url(blob_url, credential=DefaultAzureCredential())
            stream = blob_client.download_blob()
            return stream.readall()
        except Exception as e:
            logger.error("blob_download_failed", error=str(e), url=blob_url)
            return None

    async def generate_sas_url(self, blob_url: str, expiry_hours: int = 2) -> str:
        if self.settings.demo_mode:
            return blob_url + "?sas=demo"

        try:
            from datetime import datetime, timezone, timedelta
            expiry = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
            parts = blob_url.split("/")
            account_name = parts[2].split(".")[0]
            container_name = parts[3]
            blob_name = "/".join(parts[4:])

            client = self._get_client()
            if self.settings.storage_connection_string:
                # Key-based SAS (local dev)
                from azure.storage.blob import generate_blob_sas, BlobSasPermissions
                sas = generate_blob_sas(
                    account_name=account_name,
                    container_name=container_name,
                    blob_name=blob_name,
                    account_key=client.credential.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=expiry,
                )
            else:
                # User-delegation SAS (managed identity in Container Apps)
                from azure.storage.blob import generate_blob_sas, BlobSasPermissions
                udk = client.get_user_delegation_key(
                    key_start_time=datetime.now(timezone.utc),
                    key_expiry_time=expiry,
                )
                sas = generate_blob_sas(
                    account_name=account_name,
                    container_name=container_name,
                    blob_name=blob_name,
                    user_delegation_key=udk,
                    permission=BlobSasPermissions(read=True),
                    expiry=expiry,
                )
            return f"{blob_url}?{sas}"
        except Exception as e:
            logger.error("sas_generation_failed", error=str(e))
            return blob_url
