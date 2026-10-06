"""
Chat API Schemas
================

This file defines the structure of data exchanged between:

Frontend
    ↓
FastAPI
    ↓
RAG services

Pydantic validates the incoming JSON.
"""

from typing import Literal, Optional

from pydantic import BaseModel


# ==================================================
# CHAT REQUEST
# ==================================================

class ChatRequest(BaseModel):

    message: str

    session_id: str

    file_name: Optional[str] = None

    # --------------------------------------------------
    # chat:
    #     Conversational Chat Engine
    #
    # query:
    #     Router Query Engine
    # --------------------------------------------------

    mode: Literal[
        "chat",
        "query",
    ] = "chat"


# ==================================================
# SOURCE
# ==================================================

class Source(BaseModel):

    file_name: str

    text: str


# ==================================================
# CHAT RESPONSE
# ==================================================

class ChatResponse(BaseModel):

    answer: str

    sources: list[Source]