from fastapi import APIRouter
from datetime import datetime
from backend.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    settings = get_settings()
    integrations = await _check_integrations(settings)
    overall = "healthy" if all(v["ok"] for v in integrations.values()) else "degraded"
    return {
        "status": overall,
        "service": "ClaimSphere Copilot API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "demo_mode": settings.demo_mode,
        "team": "NEXORA",
        "hackathon": "LTM x Microsoft Hack2Future 2026",
        "integrations": integrations,
        "mcp_endpoint": "/mcp",
        "docs": "/docs",
    }


async def _check_integrations(settings) -> dict:
    results = {}

    # Azure OpenAI — ok if endpoint is set (key optional; managed identity used in Azure)
    results["azure_openai"] = {
        "ok": bool(settings.azure_openai_endpoint),
        "endpoint": settings.azure_openai_endpoint or "not configured",
        "auth": "api-key" if settings.azure_openai_api_key else "managed-identity",
    }

    # Azure AI Search — ok if endpoint is set (key optional; managed identity used in Azure)
    results["ai_search"] = {
        "ok": bool(settings.search_endpoint),
        "endpoint": settings.search_endpoint or "not configured",
        "index": settings.search_index_name,
        "auth": "api-key" if settings.search_admin_key else "managed-identity",
    }

    # Azure Blob Storage
    results["blob_storage"] = {
        "ok": bool(settings.storage_connection_string or settings.storage_blob_endpoint),
        "container": settings.storage_container_name,
    }

    # Dataverse — attempt a real API call to verify connectivity
    dv_ok = False
    dv_note = "not configured"
    if settings.dataverse_url and settings.dataverse_client_id and settings.dataverse_client_secret:
        try:
            from backend.tools.dataverse import DataverseClient
            client = DataverseClient()
            token = await client._get_token()
            import aiohttp
            base = settings.dataverse_url.rstrip("/")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base}/api/data/v9.2/cs_claims?$top=1",
                    headers=client._headers(token),
                ) as resp:
                    body = await resp.json()
                    if resp.status == 200:
                        dv_ok = True
                        dv_note = f"live — {len(body.get('value', []))} rows"
                    else:
                        dv_note = f"HTTP {resp.status}: {body.get('error', {}).get('message', str(body))[:120]}"
        except Exception as e:
            dv_note = str(e)[:120]
    results["dataverse"] = {
        "ok": dv_ok,
        "url": settings.dataverse_url or "not configured",
        "note": dv_note,
    }

    # Power Automate / Teams
    results["power_automate"] = {
        "ok": bool(settings.power_automate_webhook_url),
        "configured": bool(settings.power_automate_webhook_url),
    }

    # Document Intelligence — ok if endpoint is set (key optional; managed identity used in Azure)
    results["document_intelligence"] = {
        "ok": bool(settings.doc_intelligence_endpoint),
        "endpoint": settings.doc_intelligence_endpoint or "not configured",
        "auth": "api-key" if settings.doc_intelligence_key else "managed-identity",
    }

    # Application Insights
    results["application_insights"] = {
        "ok": bool(settings.applicationinsights_connection_string),
        "configured": bool(settings.applicationinsights_connection_string),
    }

    # MCP Server
    results["mcp_server"] = {
        "ok": True,
        "endpoint": "/mcp",
        "tools": 6,
        "protocol": "2025-03-26",
    }

    return results


@router.get("/")
async def root():
    return {
        "service": "ClaimSphere Copilot",
        "description": "AI-powered end-to-end insurance claims processing",
        "team": "NEXORA — LTM x Microsoft Hack2Future 2026",
        "docs": "/docs",
        "health": "/health",
        "mcp": "/mcp",
    }
