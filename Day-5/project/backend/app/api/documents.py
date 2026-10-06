"""
Document API
============

Responsibilities:

1. List uploaded documents.
2. Upload documents.
3. Trigger LlamaIndex ingestion.

FLOW
----

Frontend
    ↓
POST /api/documents/upload
    ↓
documents.py
    ↓
save file to data/documents/
    ↓
ingestion.py
    ↓
LlamaIndex
    ↓
persistent index
    ↓
response to frontend


For listing:

Frontend
    ↓
GET /api/documents
    ↓
documents.py
    ↓
data/documents/
    ↓
return ALL documents
"""

from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Query,
    UploadFile,
)

from app.config import DOCUMENTS_DIR

from app.services.ingestion import (
    ingest_documents,
)

from app.services.rag import (
    reset_index,
)


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)


# ==================================================
# SUPPORTED FILE TYPES
# ==================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".csv",
    ".docx",
}


# ==================================================
# LIST DOCUMENTS
# ==================================================

@router.get("")
async def list_documents():
    """
    Returns every supported document stored
    inside data/documents/.

    rglob() is used so documents inside nested
    directories are also discovered.
    """

    documents = []


    for path in sorted(
        DOCUMENTS_DIR.rglob("*")
    ):

        if not path.is_file():
            continue


        if path.suffix.lower() not in (
            ALLOWED_EXTENSIONS
        ):
            continue


        documents.append(
            {
                "file_name": path.name,

                "path": str(
                    path.relative_to(
                        DOCUMENTS_DIR
                    )
                ),

                "size": path.stat().st_size,

                "extension": (
                    path.suffix.lower()
                ),
            }
        )


    return {
        "count": len(documents),

        "documents": documents,
    }


# ==================================================
# DELETE DOCUMENT
# ==================================================

@router.delete("")
async def delete_document(path: str = Query(...)):
    """Delete a source file and rebuild the persisted index."""
    documents_root = DOCUMENTS_DIR.resolve()
    file_path = (DOCUMENTS_DIR / path).resolve()

    if not file_path.is_relative_to(documents_root):
        raise HTTPException(
            status_code=400,
            detail="Invalid document path.",
        )

    if (
        not file_path.is_file()
        or file_path.suffix.lower() not in ALLOWED_EXTENSIONS
    ):
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    file_name = file_path.name
    file_path.unlink()

    from app.services.chat_history import remove_document_sources

    try:
        ingest_documents()
        remove_document_sources(file_name)
    except Exception as exc:
        from app.services.ingestion import clear_index_storage

        clear_index_storage()
        reset_index()
        raise HTTPException(
            status_code=500,
            detail=(
                "The document was removed, but rebuilding the remaining "
                f"index failed: {exc}"
            ),
        ) from exc

    reset_index()

    return {
        "message": "Document and its indexed content were removed.",
        "file_name": file_name,
    }


# ==================================================
# UPLOAD DOCUMENT
# ==================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    """
    Saves a new document and rebuilds the index.

    FLOW:

        Uploaded file
              ↓
        data/documents/
              ↓
        ingest_documents()
              ↓
        nodes
              ↓
        embeddings
              ↓
        VectorStoreIndex
              ↓
        data/storage/
    """

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )


    # --------------------------------------------------
    # Prevent path traversal
    # --------------------------------------------------

    safe_filename = Path(
        file.filename
    ).name


    extension = Path(
        safe_filename
    ).suffix.lower()


    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                f"Allowed: "
                f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )


    file_path = (
        DOCUMENTS_DIR /
        safe_filename
    )


    try:

        contents = await file.read()


        # --------------------------------------------------
        # Save uploaded document
        # --------------------------------------------------

        with open(
            file_path,
            "wb",
        ) as output_file:

            output_file.write(
                contents
            )


        # --------------------------------------------------
        # Rebuild LlamaIndex
        # --------------------------------------------------

        ingest_documents()


        # --------------------------------------------------
        # Tell RAG service to reload index
        # --------------------------------------------------

        reset_index()


        return {

            "message": (
                "Document uploaded and indexed successfully."
            ),

            "file_name": safe_filename,

        }


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )