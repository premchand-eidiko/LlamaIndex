from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.chat import router as chat_router


app = FastAPI(
    title="Enterprise RAG Assistant",
    description="LlamaIndex + FastAPI RAG application",
    version="1.0.0",
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Routes
# --------------------------------------------------

app.include_router(
    documents_router
)

app.include_router(
    chat_router
)


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "Enterprise RAG Assistant API is running."
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }