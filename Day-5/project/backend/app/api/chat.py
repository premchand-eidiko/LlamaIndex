from fastapi import (
    APIRouter,
    HTTPException,
)

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)

from app.services.rag import ask_question


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    try:

        result = ask_question(
            request.message
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )