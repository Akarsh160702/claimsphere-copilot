"""
Admin API — maintenance operations for demo/test data.

Endpoints here are intended for operators preparing a clean demo run.
They clear all claim data from both the in-memory store and Dataverse.
"""
from fastapi import APIRouter
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/reset")
async def reset_all_claims():
    """
    Wipe ALL claim data — in-memory processing contexts + every row in the
    Dataverse crcce_claims table. Use before a fresh demo so the dashboard
    and Dataverse table start completely clean.
    """
    # 1. Clear the in-memory store (also clears reappearing demo seeds)
    from backend.api.claims import _processing_contexts
    in_memory_count = len(_processing_contexts)
    _processing_contexts.clear()

    # 2. Clear Dataverse + the GUID cache
    from backend.tools.dataverse import DataverseClient, _dv_errors
    dv = DataverseClient()
    dv_result = await dv.delete_all_claims()
    _dv_errors.clear()

    logger.info("admin_reset_complete", in_memory=in_memory_count, dataverse=dv_result)
    return {
        "status": "reset_complete",
        "in_memory_cleared": in_memory_count,
        "dataverse": dv_result,
        "message": "All claim data cleared. Submit new claims for a clean demo.",
    }


@router.get("/data-summary")
async def data_summary():
    """Quick count of what's currently in the in-memory store and Dataverse."""
    from backend.api.claims import _processing_contexts
    from backend.tools.dataverse import DataverseClient

    dv = DataverseClient()
    try:
        dv_rows = await dv.get_all_claims()
        dv_count = len(dv_rows)
    except Exception as e:
        dv_count = f"error: {e}"

    return {
        "in_memory_claims": len(_processing_contexts),
        "in_memory_ids": list(_processing_contexts.keys()),
        "dataverse_rows": dv_count,
    }
