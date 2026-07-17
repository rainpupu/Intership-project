"""摄像头 API 路由（桩）"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/camera", tags=["摄像头"])


@router.get("/status")
async def camera_status():
    return {"status": "ok", "message": "摄像头模块待实现"}