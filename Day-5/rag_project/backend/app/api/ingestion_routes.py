"""
Document Ingestion API Routes (Phase 17)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
from pathlib import Path
import shutil
import uuid

from app.ingestion.pipeline import ingestion_pipeline
from app.indexes.vector import get_vector_index, VectorIndex
from app.indexes.storage import index_storage
from app.schemas.models import DocumentUploadResponse
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/documents", tags=["Document Ingestion"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    department: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    access_level: Optional[str] = Form("internal"),
):
    """
    Upload and ingest an enterprise document into the RAG system.
    Supports PDF, DOCX, TXT, CSV, Markdown, and JSON.
    """
    logger.info(f"Received document upload: {file.filename}")

    # Ensure document upload directory exists
    docs_dir = Path(settings.documents_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = docs_dir / safe_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Ingest document through pipeline
        nodes = ingestion_pipeline.ingest_file(
            str(file_path),
            department=department,
            document_category=category,
            access_level=access_level,
        )

        # If vector index is active, add nodes and persist
        try:
            v_index = get_vector_index()
            # If storage context exists, save index
            storage_ctx = index_storage.create_storage_context()
            idx = v_index.create_index(nodes, show_progress=False)
            index_storage.save_index(idx)
        except Exception as e:
            logger.warning(f"Index update skipped (possibly no API key configured): {e}")

        return DocumentUploadResponse(
            success=True,
            document_id=file_id,
            file_name=file.filename or safe_filename,
            nodes_created=len(nodes),
            message=f"Successfully ingested {file.filename} into {len(nodes)} chunks.",
        )

    except Exception as e:
        logger.error(f"Error ingesting document {file.filename}: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_documents():
    """List all documents currently stored in the repository."""
    docs_dir = Path(settings.documents_dir)
    if not docs_dir.exists():
        return {"documents": [], "count": 0}

    files = [
        {
            "name": f.name,
            "size_bytes": f.stat().st_size,
            "modified": f.stat().st_mtime,
        }
        for f in docs_dir.iterdir()
        if f.is_file()
    ]
    return {"documents": files, "count": len(files)}
