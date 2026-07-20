from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.entity.db_models import User
from app.entity.schemas import (
    ApiResponse,
    BatchCatIdsRequest,
    BatchMarkCatsRequest,
    BatchToggleFocusRequest,
    CatCreate,
    CatObservationCreate,
    CatUpdate,
    ToggleFocusRequest,
)
from app.services.cat_service import cat_service


router = APIRouter(prefix="/api/cats", tags=["猫咪档案"])


def _require_admin(current_user: User) -> None:
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.get("", response_model=ApiResponse)
async def list_cats(
    keyword: str | None = None,
    adoption_status: str | None = None,
    is_focus: bool | None = None,
    db: Session = Depends(get_db),
):
    return ApiResponse(
        data=cat_service.list_cats(
            db,
            keyword=keyword,
            adoption_status=adoption_status,
            is_focus=is_focus,
        )
    )


@router.get("/{cat_id}", response_model=ApiResponse)
async def get_cat(cat_id: str, db: Session = Depends(get_db)):
    return ApiResponse(data=cat_service.get_cat(db, cat_id))


@router.post("", response_model=ApiResponse)
async def create_cat(
    request: CatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    cat = cat_service.create_cat(db, request.model_dump(exclude_unset=True), current_user)
    return ApiResponse(data=cat, message="猫咪档案创建成功")


@router.put("/{cat_id}", response_model=ApiResponse)
async def update_cat(
    cat_id: str,
    request: CatUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    cat = cat_service.update_cat(db, cat_id, request.model_dump(exclude_unset=True), current_user)
    return ApiResponse(data=cat, message="猫咪档案更新成功")


@router.delete("/{cat_id}", response_model=ApiResponse)
async def delete_cat(
    cat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    cat_service.delete_cat(db, cat_id)
    return ApiResponse(data={"success": True}, message="猫咪档案已删除")


@router.get("/{cat_id}/observations", response_model=ApiResponse)
async def list_observations(cat_id: str, db: Session = Depends(get_db)):
    return ApiResponse(data=cat_service.list_observations(db, cat_id))


@router.post("/{cat_id}/observations", response_model=ApiResponse)
async def create_observation(
    cat_id: str,
    request: CatObservationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    observation = cat_service.create_observation(db, cat_id, request.model_dump(exclude_unset=True), current_user)
    return ApiResponse(data=observation, message="观察记录已保存")


@router.get("/{cat_id}/audit-records", response_model=ApiResponse)
async def list_audit_records(
    cat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    return ApiResponse(data=cat_service.list_audit_records(db, cat_id))


@router.post("/batch-mark", response_model=ApiResponse)
async def batch_mark_cats(
    request: BatchMarkCatsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    result = cat_service.batch_mark(db, request.cat_ids, request.mark_type, request.remark, current_user)
    return ApiResponse(data=result, message=result["message"])


@router.post("/batch-unmark", response_model=ApiResponse)
async def batch_unmark_cats(
    request: BatchCatIdsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    result = cat_service.batch_unmark(db, request.cat_ids, current_user)
    return ApiResponse(data=result, message=result["message"])


@router.put("/{cat_id}/focus", response_model=ApiResponse)
async def toggle_cat_focus(
    cat_id: str,
    request: ToggleFocusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    result = cat_service.toggle_focus(db, cat_id, request.is_focus)
    return ApiResponse(data=result, message=result["message"])


@router.post("/batch-focus", response_model=ApiResponse)
async def batch_toggle_focus(
    request: BatchToggleFocusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    result = cat_service.batch_toggle_focus(db, request.cat_ids, request.is_focus)
    return ApiResponse(data=result, message=result["message"])
