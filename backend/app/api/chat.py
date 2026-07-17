"""对话 API 路由（桩）"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.get("/status")
async def chat_status():
    return {"status": "ok", "message": "对话模块待实现"}