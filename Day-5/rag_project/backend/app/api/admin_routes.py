"""
Admin and Health API Routes (Phase 17)
"""

from fastapi import APIRouter
from pathlib import Path
from app.schemas.models import HealthResponse
from app.indexes.storage import index_storage
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="", tags=["System & Admin"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check and status."""
    docs_dir = Path(settings.documents_dir)
    doc_count = len(list(docs_dir.iterdir())) if docs_dir.exists() else 0
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        index_loaded=index_storage.index_exists(),
        documents_count=doc_count,
    )


@router.delete("/admin/clear")
async def clear_system():
    """Clear all stored indexes and documents."""
    logger.warning("Clearing all persistent storage and documents")
    index_storage.clear_storage()
    docs_dir = Path(settings.documents_dir)
    if docs_dir.exists():
        for f in docs_dir.iterdir():
            if f.is_file():
                f.unlink()
    return {"status": "success", "message": "All storage and documents cleared"}
