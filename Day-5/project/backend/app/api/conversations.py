"""
Conversation API
================

This file exposes REST APIs for persistent conversations.

Frontend
    ↓
GET /api/conversations
    ↓
This file
    ↓
chat_history.py
    ↓
SQLite

The frontend never talks directly to SQLite.
"""

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.chat_history import (
    create_chat,
    delete_chat,
    get_chat,
    get_chat_messages,
    list_chats,
    update_chat_title,
)


router = APIRouter(
    prefix="/api/conversations",
    tags=["Conversations"],
)


class RenameConversationRequest(BaseModel):
    title: str


# ==================================================
# LIST PREVIOUS CHATS
# ==================================================

@router.get("")
async def get_conversations():
    """
    Returns all previous conversations.

    Used by:
        frontend/app.js

    Endpoint:
        GET /api/conversations
    """

    return {
        "conversations": list_chats()
    }


# ==================================================
# CREATE NEW CHAT
# ==================================================

@router.post("")
async def new_conversation():
    """
    Creates a new persistent chat.

    Output:

    {
        "chat_id": "...",
        "title": "New Chat"
    }
    """

    chat_id = str(uuid4())

    create_chat(
        chat_id=chat_id,
        title="New Chat",
    )

    return {
        "chat_id": chat_id,
        "title": "New Chat",
    }


# ==================================================
# GET CHAT
# ==================================================

@router.get("/{chat_id}")
async def get_conversation(
    chat_id: str,
):
    """
    Returns one conversation and all messages.
    """

    chat = get_chat(
        chat_id
    )

    if chat is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    messages = get_chat_messages(
        chat_id
    )

    return {
        "conversation": chat,
        "messages": messages,
    }


@router.patch("/{chat_id}")
async def rename_conversation(
    chat_id: str,
    request: RenameConversationRequest,
):
    """Rename a conversation shown in the frontend sidebar."""
    title = request.title.strip()
    if not title:
        raise HTTPException(
            status_code=400,
            detail="Conversation title cannot be empty.",
        )

    if get_chat(chat_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    update_chat_title(chat_id, title[:80])
    return {"chat_id": chat_id, "title": title[:80]}


# ==================================================
# DELETE CHAT
# ==================================================

@router.delete("/{chat_id}")
async def remove_conversation(
    chat_id: str,
):
    """
    Deletes one conversation.
    """

    if get_chat(chat_id) is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    delete_chat(
        chat_id
    )

    return {
        "message": "Conversation deleted."
    }