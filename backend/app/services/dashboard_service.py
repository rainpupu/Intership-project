from __future__ import annotations

from datetime import datetime, time, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.entity.db_models import Cat, RecognitionRecord


def _external_cat_id(cat: Cat) -> str:
    return cat.code or str(cat.id)


def _cat_to_dashboard_item(cat: Cat) -> dict:
    return {
        "id": _external_cat_id(cat),
        "code": cat.code,
        "name": cat.name,
        "coverImage": cat.cover_image,
        "galleryImages": cat.gallery_images or [],
        "coatColor": cat.coat_color,
        "ageStage": cat.age_stage,
        "gender": cat.gender,
        "personalityTags": cat.personality_tags or [],
        "healthStatus": cat.health_status,
        "moodStatus": cat.mood_status,
        "adoptionStatus": cat.adoption_status,
        "lastSeenLocation": cat.last_seen_location,
        "lastSeenAt": cat.last_seen_at.isoformat() if cat.last_seen_at else None,
        "description": cat.description,
        "isFocus": cat.is_focus,
        "createdAt": cat.created_at.isoformat() if cat.created_at else None,
        "updatedAt": cat.updated_at.isoformat() if cat.updated_at else None,
    }


def _record_to_dashboard_item(record: RecognitionRecord) -> dict:
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
        "healthStatus": record.health_status,
        "moodStatus": record.mood_status,
        "location": record.location,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
        "status": record.status,
    }


class DashboardService:
    @staticmethod
    def get_overview(db: Session) -> dict:
        now = datetime.now()
        today_start = datetime.combine(now.date(), time.min)
        tomorrow_start = today_start + timedelta(days=1)
        pending_filter = or_(
            Cat.is_focus.is_(True),
            Cat.mark_type.isnot(None),
            Cat.health_status.in_(["需复查", "观察中"]),
        )

        total_cats = db.query(func.count(Cat.id)).scalar() or 0
        today_recognitions = (
            db.query(func.count(RecognitionRecord.id))
            .filter(
                RecognitionRecord.created_at >= today_start,
                RecognitionRecord.created_at < tomorrow_start,
            )
            .scalar()
            or 0
        )
        pending_cats = db.query(func.count(Cat.id)).filter(pending_filter).scalar() or 0
        pending_clues = db.query(func.count(RecognitionRecord.id)).filter(RecognitionRecord.status == "线索待审核").scalar() or 0
        pending_events = pending_cats + pending_clues
        adoption_open = db.query(func.count(Cat.id)).filter(Cat.adoption_status == "待领养").scalar() or 0
        focus_cats_count = db.query(func.count(Cat.id)).filter(Cat.is_focus.is_(True)).scalar() or 0

        recent_recognitions = (
            db.query(RecognitionRecord)
            .order_by(RecognitionRecord.created_at.desc(), RecognitionRecord.id.desc())
            .limit(5)
            .all()
        )
        focus_cats = (
            db.query(Cat)
            .filter(pending_filter)
            .order_by(Cat.is_focus.desc(), Cat.updated_at.desc(), Cat.id.desc())
            .limit(5)
            .all()
        )

        return {
            "stats": {
                "totalCats": total_cats,
                "todayRecognitions": today_recognitions,
                "pendingEvents": pending_events,
                "adoptionApplications": 0,
                "adoptionOpen": adoption_open,
                "focusCats": focus_cats_count,
            },
            "recentRecognitions": [_record_to_dashboard_item(record) for record in recent_recognitions],
            "focusCats": [_cat_to_dashboard_item(cat) for cat in focus_cats],
            "recognitionTrend": DashboardService._build_recognition_trend(db, today_start),
        }

    @staticmethod
    def get_home_stats(db: Session) -> dict:
        now = datetime.now()
        today_start = datetime.combine(now.date(), time.min)
        tomorrow_start = today_start + timedelta(days=1)
        focus_filter = or_(
            Cat.is_focus.is_(True),
            Cat.mark_type.isnot(None),
            Cat.health_status.in_(["需复查", "观察中"]),
        )

        return {
            "totalCats": db.query(func.count(Cat.id)).scalar() or 0,
            "adoptionOpen": db.query(func.count(Cat.id)).filter(Cat.adoption_status == "待领养").scalar() or 0,
            "todayRecognitions": (
                db.query(func.count(RecognitionRecord.id))
                .filter(
                    RecognitionRecord.created_at >= today_start,
                    RecognitionRecord.created_at < tomorrow_start,
                )
                .scalar()
                or 0
            ),
            "focusCats": db.query(func.count(Cat.id)).filter(focus_filter).scalar() or 0,
        }

    @staticmethod
    def _build_recognition_trend(db: Session, today_start: datetime) -> list[dict]:
        start_date = today_start.date() - timedelta(days=6)
        start_time = datetime.combine(start_date, time.min)
        records = (
            db.query(RecognitionRecord.created_at)
            .filter(RecognitionRecord.created_at >= start_time)
            .all()
        )
        counts = {start_date + timedelta(days=offset): 0 for offset in range(7)}
        for (created_at,) in records:
            if created_at:
                record_date = created_at.date()
                if record_date in counts:
                    counts[record_date] += 1

        return [
            {
                "date": day.strftime("%m-%d"),
                "value": counts[day],
            }
            for day in sorted(counts)
        ]


dashboard_service = DashboardService()
