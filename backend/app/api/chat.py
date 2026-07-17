"""智能体对话 API 路由"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.services.chat_service import chat_service

router = APIRouter(prefix="/api/chat", tags=["智能体对话"])


class CreateSessionRequest(BaseModel):
    user_id: int = Field(default=1, description="用户 ID")
    title: str = Field(default="新对话", description="会话标题")


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户消息内容")


@router.post("/sessions")
async def create_session(req: CreateSessionRequest):
    session = chat_service.create_session(req.user_id, req.title)
    return {
        "id": session.id,
        "user_id": session.user_id,
        "title": session.title,
        "created_at": session.created_at,
    }


@router.get("/sessions")
async def list_sessions(user_id: int = 1):
    sessions = chat_service.list_sessions(user_id)
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "title": s.title,
            "created_at": s.created_at,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(session_id: int):
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = chat_service.get_messages(session_id)
    return {
        "id": session.id,
        "user_id": session.user_id,
        "title": session.title,
        "created_at": session.created_at,
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
            for m in messages
        ],
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int):
    deleted = chat_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"detail": "已删除"}


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: int, req: SendMessageRequest):
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    async def event_stream():
        async for sse_data in chat_service.send_message_stream(session_id, req.message):
            yield sse_data

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
