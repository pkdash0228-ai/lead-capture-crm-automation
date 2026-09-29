import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from app import chat_service
from app.routes.leads import db_dep

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str = Field(max_length=5000)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)


@router.post("")
def chat(payload: ChatRequest, request: Request, db: sqlite3.Connection = Depends(db_dep)):
    client = request.client.host if request.client else "unknown"
    if chat_service.rate_limited(client):
        raise HTTPException(429, "You're sending messages too quickly. Please wait a moment.")
    try:
        return chat_service.chat(db, payload.session_id, [m.model_dump() for m in payload.messages])
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.get("/status")
def status():
    providers = chat_service.available_providers()
    return {"providers": providers, "mode": providers[0] if providers else "offline"}
