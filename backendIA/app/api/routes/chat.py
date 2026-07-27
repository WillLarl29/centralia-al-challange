from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.llm import ChatMessage
from app.rag import CentralIAAgent

from ..deps import get_agent

router = APIRouter()


class ChatHistoryItem(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryItem] = Field(default_factory=list)


class SourceItem(BaseModel):
    id: str
    source: str
    score: float | None
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    used_fallback: bool


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, agent: CentralIAAgent = Depends(get_agent)) -> ChatResponse:
    history = [ChatMessage(role=item.role, content=item.content) for item in request.history]
    result = agent.answer(question=request.message, history=history)
    return ChatResponse(answer=result.text, sources=result.sources, used_fallback=result.used_fallback)
