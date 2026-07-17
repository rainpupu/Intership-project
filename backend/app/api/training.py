"""训练 API 路由（桩）"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/training", tags=["训练"])


@router.get("/status")
async def training_status():
    return {"status": "ok", "message": "训练模块待实现"}