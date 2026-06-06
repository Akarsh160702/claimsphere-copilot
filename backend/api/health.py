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

    # Azure OpenAI
    results["azure_openai"] = {
        "ok": bool(settings.azure_openai_endpoint and settings.azure_openai_api_key),
        "endpoint": settings.azure_openai_endpoint or "not configured",
    }

    # Azure AI Search
    results["ai_search"] = {
        "ok": bool(settings.search_endpoint and settings.search_admin_key),
        "endpoint": settings.search_endpoint or "not configured",
        "index": settings.search_index_name,
    }

    # Azure Blob Storage
    results["blob_storage"] = {
        "ok": bool(settings.storage_connection_string or settings.storage_blob_endpoint),
        "container": settings.storage_container_name,
    }

    # Dataverse
    results["dataverse"] = {
        "ok": bool(
            settings.dataverse_url
            and settings.dataverse_client_id
            and settings.dataverse_client_secret
        ),
        "url": settings.dataverse_url or "not configured",
        "note": "falls back to in-memory if unavailable",
    }

    # Power Automate / Teams
    results["power_automate"] = {
        "ok": bool(settings.power_automate_webhook_url),
        "configured": bool(settings.power_automate_webhook_url),
    }

    # Document Intelligence
    results["document_intelligence"] = {
        "ok": bool(settings.doc_intelligence_endpoint and settings.doc_intelligence_key),
        "endpoint": settings.doc_intelligence_endpoint or "not configured",
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
