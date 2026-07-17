"""
健康检查 API 路由
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.config.settings import settings
from app.core.logger import get_logger

logger = get_logger("health")

router = APIRouter(prefix="/api/health", tags=["健康检查"])


@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/database")
async def database_health():
    try:
        from app.database.session import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected", "message": "数据库连接正常"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "message": f"数据库连接失败: {str(e)}"})