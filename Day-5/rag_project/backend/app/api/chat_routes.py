"""
Conversational Chat API Routes (Phase 17)
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.schemas.models import ChatRequest, ChatResponse, Source
from app.chat.engine import chat_manager
from app.indexes.storage import index_storage
from app.core.logging import logger

router = APIRouter(prefix="/chat", tags=["Conversational Chat"])


@router.post("", response_model=ChatResponse)
async def chat_interaction(request: ChatRequest):
    """
    Multi-turn Conversational RAG endpoint with session memory.
    """
    logger.info(f"Chat request for session {request.session_id}: '{request.message}'")

    session = chat_manager.get_or_create_session(request.session_id)

    # Check if index exists and attempt Conversational RAG
    if index_storage.index_exists():
        try:
            index = index_storage.load_index()
            chat_engine = chat_manager.create_chat_engine(index, request.session_id)
            response = chat_engine.chat(request.message)

            # Record turn in API history (chat_engine already stored turn in memory)
            session.record_turn(request.message, str(response))

            sources = [
                Source(file_name=n.node.metadata.get("file_name", "document"), metadata=n.node.metadata)
                for n in (getattr(response, "source_nodes", None) or [])
            ]

            return ChatResponse(
                response=str(response),
                sources=sources,
                session_id=request.session_id,
                conversation_history=session.history,
            )
        except Exception as e:
            logger.warning(f"RAG chat engine error, falling back to direct LLM chat: {e}", exc_info=True)

    # Fallback to direct LLM chat with session memory
    result = chat_manager.chat_with_llm(request.session_id, request.message)
    return ChatResponse(
        response=result["response"],
        sources=result.get("sources", []),
        session_id=request.session_id,
        conversation_history=session.history,
    )


@router.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """Retrieve all historical messages for a given session."""
    session = chat_manager.get_or_create_session(session_id)
    return {
        "session_id": session_id,
        "message_count": len(session.history),
        "history": session.history,
    }


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Reset and clear memory for a session."""
    if session_id in chat_manager.sessions:
        del chat_manager.sessions[session_id]
        return {"status": "cleared", "session_id": session_id}
    return {"status": "not_found", "session_id": session_id}
