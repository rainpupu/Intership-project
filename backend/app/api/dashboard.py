"""仪表盘 API 路由（桩）"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


@router.get("/status")
async def dashboard_status():
    return {"status": "ok", "message": "仪表盘模块待实现"}