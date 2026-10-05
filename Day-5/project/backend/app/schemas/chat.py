from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class Source(BaseModel):
    file_name: str
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]