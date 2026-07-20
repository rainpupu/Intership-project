from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.entity.db_models import RecognitionRecord, User


def _record_to_dict(record: RecognitionRecord) -> dict:
    return {
        "id": f"rec-{record.id}",
        "userId": str(record.user_id),
        "image": record.image,
        "catId": record.cat_id,
        "catName": record.cat_name,
        "similarity": record.similarity,
        "healthStatus": record.health_status,
        "moodStatus": record.mood_status,
        "location": record.location,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "status": record.status,
    }


class RecognitionHistoryService:
    @staticmethod
    def create_from_analysis(db: Session, current_user: User, result: dict[str, Any]) -> dict:
        candidates = result.get("candidates") or []
        uploaded_images = result.get("uploadedImages") or []
        analysis = result.get("analysis") or {}
        top_candidate = candidates[0] if candidates else {}
        detected_count = int(result.get("detectedCount") or 0)

        if top_candidate:
            image = top_candidate.get("image") or top_candidate.get("cropImage") or (uploaded_images[0] if uploaded_images else "")
            cat_id = top_candidate.get("catId")
            cat_name = top_candidate.get("name") or "未知猫咪"
            similarity = float(top_candidate.get("similarity") or 0)
            status = top_candidate.get("status") or "已识别"
            health_status = top_candidate.get("healthStatus")
            mood_status = top_candidate.get("moodStatus")
        else:
            image = uploaded_images[0] if uploaded_images else ""
            cat_id = None
            cat_name = "未识别到猫咪"
            similarity = 0.0
            status = "未检测到"
            health_status = None
            mood_status = None

        record = RecognitionRecord(
            user_id=current_user.id,
            image=image,
            cat_id=cat_id,
            cat_name=cat_name,
            similarity=similarity,
            health_status=health_status,
            mood_status=mood_status,
            location="用户上传",
            status=status,
            analysis_summary=analysis.get("summary"),
            detected_count=detected_count,
            elapsed_ms=int(round(float(result.get("elapsedMs") or 0))),
            candidates=candidates,
            created_at=datetime.now(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return _record_to_dict(record)

    @staticmethod
    def list_records(db: Session, current_user: User, scope: str = "mine") -> list[dict]:
        query = db.query(RecognitionRecord)
        if scope != "all" or current_user.role not in ("admin", "super_admin"):
            query = query.filter(RecognitionRecord.user_id == current_user.id)

        records = query.order_by(RecognitionRecord.created_at.desc(), RecognitionRecord.id.desc()).all()
        return [_record_to_dict(record) for record in records]


recognition_history_service = RecognitionHistoryService()
