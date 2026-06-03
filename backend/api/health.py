from fastapi import APIRouter
from datetime import datetime
from backend.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "ClaimSphere Copilot API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "demo_mode": settings.demo_mode,
        "team": "NEXORA",
        "hackathon": "LTM x Microsoft Hack2Future 2026",
    }


@router.get("/")
async def root():
    return {
        "service": "ClaimSphere Copilot",
        "description": "AI-powered end-to-end insurance claims processing",
        "docs": "/docs",
        "health": "/health",
    }
