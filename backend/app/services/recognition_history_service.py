from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.entity.db_models import RecognitionRecord, User


def _record_to_dict(record: RecognitionRecord) -> dict:
    candidates = record.candidates or []
    top_candidate = candidates[0] if candidates else {}
    return {
        "id": f"rec-{record.id}",
        "userId": str(record.user_id),
        "image": record.image,
        "catId": record.cat_id,
        "catName": record.cat_name,
        "similarity": record.similarity,
        "modelType": top_candidate.get("modelType"),
        "breedName": top_candidate.get("breedName"),
        "breedConfidence": top_candidate.get("breedConfidence"),
        "identityStatus": top_candidate.get("identityStatus"),
        "bestIdentityMatch": top_candidate.get("bestIdentityMatch"),
        "healthStatus": record.health_status,
        "moodStatus": record.mood_status,
        "location": record.location,
        "observedAt": record.observed_at.isoformat() if record.observed_at else None,
        "userRemark": record.user_remark,
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
            status="个人识别" if status not in ("未检测到",) else status,
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
        if scope == "clues":
            if current_user.role not in ("admin", "super_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")
            query = query.filter(RecognitionRecord.status == "线索待审核")
        elif scope == "all":
            if current_user.role not in ("admin", "super_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")
        else:
            query = query.filter(RecognitionRecord.user_id == current_user.id)

        records = query.order_by(RecognitionRecord.created_at.desc(), RecognitionRecord.id.desc()).all()
        return [_record_to_dict(record) for record in records]

    @staticmethod
    def count_pending_clues(db: Session, current_user: User) -> dict:
        if current_user.role not in ("admin", "super_admin"):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        count = db.query(RecognitionRecord).filter(RecognitionRecord.status == "线索待审核").count()
        return {"count": count}

    @staticmethod
    def submit_campus_clue(db: Session, record_id: str, payload: dict[str, Any], current_user: User) -> dict:
        record_pk = RecognitionHistoryService._parse_record_id(record_id)
        record = db.query(RecognitionRecord).filter(RecognitionRecord.id == record_pk).first()
        if not record:
            raise HTTPException(status_code=404, detail="识别记录不存在")
        if record.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="不能提交其他账号的识别记录")
        if record.status in ("已确认", "已建档"):
            raise HTTPException(status_code=400, detail="该记录已经被管理员处理，不能重复提交")

        location = (payload.get("location") or "").strip()
        if not location:
            raise HTTPException(status_code=400, detail="提交校园线索必须填写拍摄地点")

        record.location = location
        record.observed_at = payload.get("observed_at") or datetime.now()
        record.user_remark = (payload.get("user_remark") or "").strip() or None
        record.status = "线索待审核"
        db.commit()
        db.refresh(record)
        return _record_to_dict(record)

    @staticmethod
    def dismiss_campus_clue(db: Session, record_id: str, current_user: User) -> dict:
        if current_user.role not in ("admin", "super_admin"):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        record_pk = RecognitionHistoryService._parse_record_id(record_id)
        record = db.query(RecognitionRecord).filter(RecognitionRecord.id == record_pk).first()
        if not record:
            raise HTTPException(status_code=404, detail="识别记录不存在")
        if record.status != "线索待审核":
            raise HTTPException(status_code=400, detail="只有待审核线索可以忽略")

        record.status = "线索已忽略"
        db.commit()
        db.refresh(record)
        return _record_to_dict(record)

    @staticmethod
    def _parse_record_id(record_id: str) -> int:
        raw = record_id.removeprefix("rec-")
        if not raw.isdigit():
            raise HTTPException(status_code=400, detail="识别记录编号无效")
        return int(raw)


recognition_history_service = RecognitionHistoryService()
