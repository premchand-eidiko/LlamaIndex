"""
Enterprise RAG Assistant - Main Application (Phase 17)

Production-grade modular FastAPI RAG system using LlamaIndex.
Exposes modular routes for document ingestion, retrieval, re-ranking,
hybrid search, conversational chat, streaming, and GraphRAG.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uvicorn

from app.api.ingestion_routes import router as ingestion_router
from app.api.query_routes import router as query_router
from app.api.chat_routes import router as chat_router
from app.api.graph_routes import router as graph_router
from app.api.admin_routes import router as admin_router

from app.indexes.vector import EmbeddingModel
from app.indexes.storage import index_storage
from app.core.exceptions import EnterpriseRAGException
from app.core.llm import get_llm
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(
    title="Enterprise RAG Assistant",
    description="Full-scale Enterprise RAG Platform built with LlamaIndex and FastAPI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log incoming requests and compute execution latency."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000.0
    logger.info(
        f"{request.method} {request.url.path} -> Status {response.status_code} "
        f"({duration_ms:.2f}ms)"
    )
    return response


@app.exception_handler(EnterpriseRAGException)
async def enterprise_exception_handler(request: Request, exc: EnterpriseRAGException):
    """Handle domain-specific Enterprise RAG exceptions with standardized error JSON."""
    logger.error(f"Enterprise Exception on {request.url.path}: {exc.message} (status={exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
        },
    )


@app.on_event("startup")
async def startup_event():
    """Initialize core RAG components on application boot."""
    logger.info("Starting Enterprise RAG Platform...")
    from llama_index.core import Settings as LlamaSettings
    try:
        llm = get_llm()
        if llm is not None:
            LlamaSettings.llm = llm
            logger.info("LLM engine successfully initialized and registered in LlamaIndex Settings.")
    except Exception as e:
        logger.warning(f"LLM initialization deferred: {e}")

    try:
        embed_model = EmbeddingModel()
        if embed_model.embedding_model is not None:
            LlamaSettings.embed_model = embed_model.embedding_model
            logger.info("Embedding Model successfully initialized and registered in LlamaIndex Settings.")
        else:
            logger.warning("Running without configured embedding key. Vector indexing will run in mock/concept mode.")
    except Exception as e:
        logger.warning(f"Embedding initialization deferred: {e}")

    if index_storage.index_exists():
        logger.info(f"Existing document index found in {settings.storage_dir}.")
    else:
        logger.info(f"No existing index found in {settings.storage_dir}. System ready for first upload.")


# Include API Routers under /api/v1
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(graph_router, prefix="/api/v1")

# Also include top-level routers for root convenience and backward compatibility
app.include_router(admin_router)
app.include_router(ingestion_router)
app.include_router(query_router)
app.include_router(chat_router)
app.include_router(graph_router)


@app.get("/")
async def root():
    """Root endpoint welcoming users and directing to API documentation."""
    return {
        "message": "Enterprise RAG Assistant API is online",
        "docs_url": "/docs",
        "version": "2.0.0",
        "phases_active": "Phases 1 through 20 enabled",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
