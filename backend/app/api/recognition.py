from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.services.yolo_recognition_service import yolo_recognition_service


router = APIRouter(prefix="/api/recognition", tags=["recognition"])


@router.post("/analyze")
async def analyze_images(
    request: Request,
    files: list[UploadFile] = File(...),
    conf_threshold: float = 0.25,
):
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片")

    try:
        return await yolo_recognition_service.analyze_uploads(
            files=files,
            base_url=str(request.base_url),
            conf_threshold=conf_threshold,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
