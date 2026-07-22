from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.entity.db_models import User
from app.entity.schemas import ApiResponse, CloudAdoptionOrderCreate
from app.services.cloud_adoption_service import cloud_adoption_service


router = APIRouter(prefix="/api/cloud-adoptions", tags=["云领养订单"])


def _require_admin(current_user: User) -> None:
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.post("", response_model=ApiResponse)
async def create_cloud_adoption_order(
    request: CloudAdoptionOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = cloud_adoption_service.create_order(db, request.model_dump(exclude_unset=True), current_user)
    return ApiResponse(data=order, message="云领养订单已记录")


@router.get("", response_model=ApiResponse)
async def list_cloud_adoption_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    return ApiResponse(data=cloud_adoption_service.list_orders(db))
