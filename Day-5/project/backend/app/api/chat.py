"""
Chat API
========

This is the main entry point for questions.

Frontend
    ↓
POST /api/chat
    ↓
This file
    ↓
RAG service
    ↓
LlamaIndex
    ↓
Groq
    ↓
Answer
    ↓
This file
    ↓
Save answer to SQLite
    ↓
Frontend
"""

from fastapi import (
    APIRouter,
    HTTPException,
)

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)

from app.services.chat_history import (
    add_message,
    create_chat,
    get_chat,
    get_chat_messages,
    update_chat_title,
)

from app.services.rag import (
    ask_question,
    chat_question,
    reset_chat_session,
)


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


# ==================================================
# MAIN CHAT ENDPOINT
# ==================================================

@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
):
    """
    Main conversational endpoint.

    FLOW
    ----
    Frontend
        ↓
    POST /api/chat
        ↓
    validate request
        ↓
    ensure chat exists
        ↓
    save user message
        ↓
    RAG / Chat Engine
        ↓
    save assistant response
        ↓
    return answer + sources
    """

    if not request.message.strip():

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )


    # --------------------------------------------------
    # Make sure the conversation exists
    # --------------------------------------------------

    conversation = get_chat(request.session_id)
    if conversation is None:

        create_chat(
            chat_id=request.session_id,
            title=request.message.strip().splitlines()[0][:50],
        )
    elif (
        conversation["title"] == "New Chat"
        and not get_chat_messages(request.session_id)
    ):
        title = request.message.strip().splitlines()[0][:50]
        update_chat_title(request.session_id, title)


    # --------------------------------------------------
    # Save user's message
    # --------------------------------------------------

    add_message(
        chat_id=request.session_id,
        role="user",
        content=request.message,
    )


    try:

        # ==================================================
        # CHAT ENGINE
        # ==================================================

        if request.mode == "chat":

            result = chat_question(

                question=request.message,

                session_id=request.session_id,

                file_name=request.file_name,
            )


        # ==================================================
        # ROUTER QUERY ENGINE
        # ==================================================

        else:

            result = ask_question(

                question=request.message,

                file_name=request.file_name,
            )


        # --------------------------------------------------
        # Save assistant response
        # --------------------------------------------------

        add_message(

            chat_id=request.session_id,

            role="assistant",

            content=result["answer"],

            sources=result.get(
                "sources",
                [],
            ),
        )


        # --------------------------------------------------
        # Return to frontend
        # --------------------------------------------------

        return result


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ==================================================
# RESET CHAT
# ==================================================

@router.post("/reset")
async def reset_chat(
    request: ChatRequest,
):
    """
    Clears temporary LlamaIndex session state.

    Persistent SQLite history is NOT deleted.

    This distinction is important:

        reset_chat_session()
             ↓
        temporary runtime memory

        SQLite
             ↓
        permanent history
    """

    reset_chat_session(
        request.session_id
    )

    return {
        "message": "Chat session reset."
    }