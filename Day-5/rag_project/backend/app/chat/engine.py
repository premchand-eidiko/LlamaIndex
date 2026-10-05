"""
Conversational RAG Module (Phase 15)

This module implements multi-turn conversational chat with memory buffers,
context condensing, and session management.

Why we need Conversational RAG:
- Users naturally converse with follow-ups ("Can I carry it over?", "What about part-time?").
- Conversational RAG remembers previous turns and resolves pronouns using conversation history.
- Manages separate session states across different users.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from llama_index.core import VectorStoreIndex
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine, ContextChatEngine
from llama_index.core.llms import ChatMessage, MessageRole
from loguru import logger

from app.schemas.models import ChatMessage as APIChatMessage, Source
from app.core.config import settings
from app.core.llm import get_llm


class ConversationalSession:
    """Manages chat memory and message history for a single user session."""

    def __init__(self, session_id: str, token_limit: int = 3000):
        self.session_id = session_id
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=token_limit)
        self.history: List[APIChatMessage] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def record_turn(self, user_msg: str, assistant_msg: str):
        """Record turn in API history when engine already updated internal memory."""
        self.history.append(APIChatMessage(role="user", content=user_msg))
        self.history.append(APIChatMessage(role="assistant", content=assistant_msg))
        self.updated_at = datetime.utcnow()

    def add_user_message(self, content: str):
        """Add user message to both LlamaIndex memory and API history."""
        self.memory.put(ChatMessage(role=MessageRole.USER, content=content))
        self.history.append(APIChatMessage(role="user", content=content))
        self.updated_at = datetime.utcnow()

    def add_assistant_message(self, content: str):
        """Add assistant message to both LlamaIndex memory and API history."""
        self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=content))
        self.history.append(APIChatMessage(role="assistant", content=content))
        self.updated_at = datetime.utcnow()


class EnterpriseChatManager:
    """
    Manager for conversational RAG sessions and chat engines.
    """

    def __init__(self):
        self.sessions: Dict[str, ConversationalSession] = {}
        logger.info("Initialized EnterpriseChatManager")

    def get_or_create_session(self, session_id: str) -> ConversationalSession:
        """Get existing session or create a new one."""
        if session_id not in self.sessions:
            logger.info(f"Creating new conversational session: {session_id}")
            self.sessions[session_id] = ConversationalSession(session_id)
        return self.sessions[session_id]

    def create_chat_engine(
        self,
        index: VectorStoreIndex,
        session_id: str,
    ) -> CondensePlusContextChatEngine:
        """Create a CondensePlusContextChatEngine attached to the session memory with Groq LLM."""
        session = self.get_or_create_session(session_id)
        retriever = index.as_retriever(similarity_top_k=settings.similarity_top_k)
        llm = get_llm()

        system_prompt = (
            "You are an intelligent Enterprise AI Assistant. "
            "You remember the conversation history, greet users warmly, and maintain context across turns. "
            "If the user asks about their identity, name, or conversational details they shared during this chat, use the conversation history to answer. "
            "For company policies, documents, procedures, or technical questions, ground your answers in the retrieved context. "
            "If information is not found in the documents or conversation history, politely state so."
        )

        chat_engine = CondensePlusContextChatEngine.from_defaults(
            retriever=retriever,
            llm=llm,
            memory=session.memory,
            system_prompt=system_prompt,
            verbose=True,
        )
        return chat_engine

    def chat_with_llm(self, session_id: str, message: str) -> Dict[str, Any]:
        """Chat directly with LLM preserving session memory when index is unavailable or empty."""
        session = self.get_or_create_session(session_id)
        llm = get_llm()
        if llm:
            try:
                system_msg = ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=(
                        "You are an intelligent Enterprise AI Assistant. "
                        "You remember the conversation history, greet users warmly, and maintain context across turns. "
                        "If the user shares personal details like their name, remember it and use it when asked."
                    ),
                )
                history_messages = session.memory.get()
                current_messages = [system_msg] + list(history_messages) + [ChatMessage(role=MessageRole.USER, content=message)]

                response = llm.chat(current_messages)
                reply = str(response.message.content)
                session.add_user_message(message)
                session.add_assistant_message(reply)
                return {
                    "response": reply,
                    "session_id": session_id,
                    "turns": len(session.history),
                    "sources": [],
                }
            except Exception as e:
                logger.error(f"Direct LLM chat error: {e}")

        return self.chat_mock_response(session_id, message)

    def chat_mock_response(self, session_id: str, message: str) -> Dict[str, Any]:
        """Provide informative fallback when LLM is unavailable."""
        session = self.get_or_create_session(session_id)
        session.add_user_message(message)
        reply = (
            f"I received your message: '{message}'. "
            "AI generation is currently in offline mode. Please ensure GROQ_API_KEY is configured."
        )
        session.add_assistant_message(reply)

        return {
            "response": reply,
            "session_id": session_id,
            "turns": len(session.history),
            "sources": [],
        }


# Global singleton
chat_manager = EnterpriseChatManager()
