"""
FastAPI Application Entry Point
================================

This is the STARTING POINT of the backend.

When we execute:

    uvicorn app.main:app --reload

Uvicorn imports:

    app.main

and looks for:

    app

This file then connects all API routers.

ARCHITECTURE
------------

Uvicorn
   ↓
main.py
   │
   ├── documents.py
   │
   ├── chat.py
   │
   └── conversations.py
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import (
    router as chat_router,
)

from app.api.conversations import (
    router as conversations_router,
)

from app.api.documents import (
    router as documents_router,
)

from app.services.chat_history import (
    initialize_database,
)


# ==================================================
# APPLICATION STARTUP
# ==================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs when FastAPI starts.

    Currently:
        initialize SQLite database
    """

    initialize_database()

    yield


# ==================================================
# FASTAPI APPLICATION
# ==================================================

app = FastAPI(

    title="Enterprise RAG Assistant",

    description=(
        "Enterprise document assistant "
        "using LlamaIndex, FastAPI and Groq."
    ),

    version="2.0.0",

    lifespan=lifespan,
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ==================================================
# API ROUTERS
# ==================================================

# Document APIs:
#
# GET  /api/documents
# POST /api/documents/upload

app.include_router(
    documents_router
)


# Chat APIs:
#
# POST /api/chat
# POST /api/chat/reset

app.include_router(
    chat_router
)


# Conversation APIs:
#
# GET    /api/conversations
# POST   /api/conversations
# GET    /api/conversations/{chat_id}
# DELETE /api/conversations/{chat_id}

app.include_router(
    conversations_router
)


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/")
async def root():

    return {
        "message": (
            "Enterprise RAG Assistant API is running."
        )
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy"
    }