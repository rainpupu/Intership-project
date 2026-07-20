from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.entity.db_models import User
from app.entity.schemas import ApiResponse
from app.services.dashboard_service import dashboard_service


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _is_admin(user: User) -> bool:
    return user.role in ("admin", "super_admin")


@router.get("/status")
async def dashboard_status():
    return {"status": "ok", "message": "dashboard module ready"}


@router.get("/overview", response_model=ApiResponse)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _is_admin(current_user):
        return ApiResponse(code=403, message="需要管理员权限", data=None)
    return ApiResponse(data=dashboard_service.get_overview(db))


@router.get("/home-stats", response_model=ApiResponse)
async def get_home_stats(db: Session = Depends(get_db)):
    return ApiResponse(data=dashboard_service.get_home_stats(db))
