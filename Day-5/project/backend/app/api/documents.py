from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.config import DOCUMENTS_DIR
from app.services.ingestion import ingest_documents
from app.services.rag import reset_index


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".csv",
    ".docx",
}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    """
    Upload a document and rebuild the RAG index.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            ),
        )

    file_path = (
        DOCUMENTS_DIR / file.filename
    )

    try:

        contents = await file.read()

        with open(
            file_path,
            "wb",
        ) as output_file:
            output_file.write(contents)

        # Rebuild index with all documents
        ingest_documents()

        # Force query service to reload it
        reset_index()

        return {
            "message": "Document uploaded successfully.",
            "file_name": file.filename,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )