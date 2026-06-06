"""
ClaimSphere Copilot — FastAPI Application Entry Point
Team NEXORA | LTM x Microsoft Hack2Future 2026
"""
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# Azure Application Insights — auto-instruments FastAPI, aiohttp, OpenAI client.
# Sends distributed traces, requests, and exceptions to Azure Monitor.
try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    _ai_conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    if _ai_conn:
        configure_azure_monitor(connection_string=_ai_conn)
except Exception:
    pass  # Silently skip if not configured or package unavailable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from backend.api import claims, documents, health, support, mock, webhooks
from backend.config import get_settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "claimsphere_starting",
        demo_mode=settings.demo_mode,
        env=settings.app_env,
    )
    if settings.demo_mode:
        logger.info("DEMO MODE ACTIVE — using mock data, no Azure credentials required")

    # Seed policies into AI Search on startup (if not demo mode)
    if not settings.demo_mode and settings.search_endpoint:
        try:
            from backend.tools.ai_search import AISearchClient
            from backend.data_seeder import seed_policies
            client = AISearchClient()
            await seed_policies(client)
            logger.info("policies_seeded_to_search")
        except Exception as e:
            logger.warning("policy_seeding_failed", error=str(e))

    # Pre-populate the in-memory claims store so the dashboard shows live
    # data immediately on a cold start (no LLM calls — instant).
    try:
        from backend.api.claims import _processing_contexts
        from backend.data_seeder import seed_demo_claims
        if not _processing_contexts:  # Only seed if store is empty
            seed_demo_claims(_processing_contexts)
    except Exception as e:
        logger.warning("demo_claims_seeding_failed", error=str(e))

    yield
    logger.info("claimsphere_shutting_down")


app = FastAPI(
    title="ClaimSphere Copilot API",
    description=(
        "AI-powered end-to-end insurance claims processing system. "
        "Built by Team NEXORA for LTM x Microsoft Hack2Future 2026."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(claims.router)
app.include_router(documents.router)
app.include_router(support.router)
app.include_router(mock.router)
app.include_router(webhooks.router)

# MCP (Model Context Protocol) server — exposes ClaimSphere tools to any MCP
# client: Copilot Studio, Claude Desktop, VS Code Copilot Agent.
from backend.api import mcp as mcp_module
app.include_router(mcp_module.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
