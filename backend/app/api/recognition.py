from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.entity.db_models import User
from app.entity.schemas import ApiResponse, ConfirmExistingCatRequest, CreateCatFromRecognitionRequest
from app.services.individual_recognition_service import individual_recognition_service
from app.services.recognition_history_service import recognition_history_service
from app.services.yolo_recognition_service import yolo_recognition_service


router = APIRouter(prefix="/api/recognition", tags=["recognition"])


@router.post("/analyze")
async def analyze_images(
    request: Request,
    files: list[UploadFile] = File(...),
    conf_threshold: float = 0.25,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片")

    try:
        result = await yolo_recognition_service.analyze_uploads(
            files=files,
            base_url=str(request.base_url),
            conf_threshold=conf_threshold,
            db=db,
        )
        result["record"] = recognition_history_service.create_from_analysis(db, current_user, result)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/records", response_model=ApiResponse)
async def list_recognition_records(
    scope: str = "mine",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if scope == "all" and current_user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    records = recognition_history_service.list_records(db, current_user, scope)
    return ApiResponse(data=records)


@router.post("/records/{record_id}/confirm-existing", response_model=ApiResponse)
async def confirm_existing_cat(
    record_id: str,
    request: ConfirmExistingCatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = individual_recognition_service.attach_record_to_cat(db, record_id, request.cat_id, current_user)
    return ApiResponse(data=result, message=result["message"])


@router.post("/records/{record_id}/create-cat", response_model=ApiResponse)
async def create_cat_from_recognition(
    record_id: str,
    request: CreateCatFromRecognitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = individual_recognition_service.create_cat_from_record(
        db,
        record_id,
        request.model_dump(exclude_unset=True),
        current_user,
    )
    return ApiResponse(data=result, message=result["message"])
