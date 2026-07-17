"""知识库 API 路由（桩）"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.get("/status")
async def knowledge_status():
    return {"status": "ok", "message": "知识库模块待实现"}