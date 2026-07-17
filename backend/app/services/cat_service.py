from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.entity.db_models import Cat, CatAuditRecord, CatObservation, User


CAT_UPDATABLE_FIELDS = [
    "code",
    "name",
    "cover_image",
    "gallery_images",
    "coat_color",
    "age_stage",
    "gender",
    "personality_tags",
    "health_status",
    "mood_status",
    "adoption_status",
    "last_seen_location",
    "last_seen_at",
    "description",
    "is_focus",
]


def _operator_name(user: Optional[User]) -> str:
    if not user:
        return "系统"
    return user.nickname or user.phone or user.username


def _external_id(cat: Cat) -> str:
    return cat.code or str(cat.id)


def _cat_to_dict(cat: Cat) -> dict:
    return {
        "id": _external_id(cat),
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
        "_markType": cat.mark_type,
        "_markRemark": cat.mark_remark,
        "createdAt": cat.created_at.isoformat() if cat.created_at else None,
        "updatedAt": cat.updated_at.isoformat() if cat.updated_at else None,
    }


def _observation_to_dict(observation: CatObservation) -> dict:
    return {
        "id": f"obs-{observation.id}",
        "catId": _external_id(observation.cat),
        "location": observation.location,
        "moodStatus": observation.mood_status,
        "healthStatus": observation.health_status,
        "observedAt": observation.observed_at.isoformat() if observation.observed_at else None,
        "description": observation.description,
        "createdAt": observation.created_at.isoformat() if observation.created_at else None,
    }


def _audit_record_to_dict(record: CatAuditRecord) -> dict:
    return {
        "id": f"audit-{record.id}",
        "catId": _external_id(record.cat),
        "action": record.action,
        "remark": record.remark or "",
        "operator": record.operator_name or "系统",
        "operatedAt": record.operated_at.isoformat() if record.operated_at else None,
    }


class CatService:
    @staticmethod
    def resolve_cat(db: Session, cat_id: str) -> Cat:
        query = db.query(Cat)
        if cat_id.isdigit():
            cat = query.filter(or_(Cat.id == int(cat_id), Cat.code == cat_id)).first()
        else:
            cat = query.filter(Cat.code == cat_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="猫咪档案不存在")
        return cat

    @staticmethod
    def list_cats(
        db: Session,
        keyword: Optional[str] = None,
        adoption_status: Optional[str] = None,
        is_focus: Optional[bool] = None,
    ) -> list[dict]:
        query = db.query(Cat)
        if keyword:
            keyword_like = f"%{keyword}%"
            query = query.filter(
                or_(
                    Cat.code.ilike(keyword_like),
                    Cat.name.ilike(keyword_like),
                    Cat.coat_color.ilike(keyword_like),
                    Cat.last_seen_location.ilike(keyword_like),
                )
            )
        if adoption_status:
            query = query.filter(Cat.adoption_status == adoption_status)
        if is_focus is not None:
            query = query.filter(Cat.is_focus == is_focus)

        cats = query.order_by(Cat.is_focus.desc(), Cat.updated_at.desc(), Cat.id.desc()).all()
        return [_cat_to_dict(cat) for cat in cats]

    @staticmethod
    def get_cat(db: Session, cat_id: str) -> dict:
        return _cat_to_dict(CatService.resolve_cat(db, cat_id))

    @staticmethod
    def create_cat(db: Session, payload: dict, current_user: Optional[User] = None) -> dict:
        code = payload.get("code") or f"cat-{int(datetime.now().timestamp())}"
        if db.query(Cat).filter(Cat.code == code).first():
            raise HTTPException(status_code=409, detail="猫咪编号已存在")

        cat = Cat(
            code=code,
            created_by_id=current_user.id if current_user else None,
        )
        for field in CAT_UPDATABLE_FIELDS:
            if field in payload and payload[field] is not None:
                setattr(cat, field, payload[field])
        cat.code = code

        db.add(cat)
        db.commit()
        db.refresh(cat)
        CatService._add_audit_record(db, cat, "审核通过", "创建猫咪档案", current_user)
        return _cat_to_dict(cat)

    @staticmethod
    def update_cat(db: Session, cat_id: str, payload: dict, current_user: Optional[User] = None) -> dict:
        cat = CatService.resolve_cat(db, cat_id)
        if "code" in payload and payload["code"] and payload["code"] != cat.code:
            existing = db.query(Cat).filter(Cat.code == payload["code"], Cat.id != cat.id).first()
            if existing:
                raise HTTPException(status_code=409, detail="猫咪编号已存在")

        for field in CAT_UPDATABLE_FIELDS:
            if field in payload and payload[field] is not None:
                setattr(cat, field, payload[field])
        db.commit()
        db.refresh(cat)
        CatService._add_audit_record(db, cat, "审核通过", "更新猫咪档案", current_user)
        return _cat_to_dict(cat)

    @staticmethod
    def delete_cat(db: Session, cat_id: str) -> None:
        cat = CatService.resolve_cat(db, cat_id)
        db.delete(cat)
        db.commit()

    @staticmethod
    def list_observations(db: Session, cat_id: str) -> list[dict]:
        cat = CatService.resolve_cat(db, cat_id)
        observations = (
            db.query(CatObservation)
            .filter(CatObservation.cat_id == cat.id)
            .order_by(CatObservation.observed_at.desc())
            .all()
        )
        return [_observation_to_dict(observation) for observation in observations]

    @staticmethod
    def create_observation(db: Session, cat_id: str, payload: dict, current_user: Optional[User] = None) -> dict:
        cat = CatService.resolve_cat(db, cat_id)
        observation = CatObservation(
            cat_id=cat.id,
            location=payload.get("location"),
            mood_status=payload.get("mood_status"),
            health_status=payload.get("health_status"),
            observed_at=payload.get("observed_at") or datetime.now(),
            description=payload.get("description"),
            created_by_id=current_user.id if current_user else None,
        )
        db.add(observation)

        if observation.location:
            cat.last_seen_location = observation.location
        if observation.mood_status:
            cat.mood_status = observation.mood_status
        if observation.health_status:
            cat.health_status = observation.health_status
        cat.last_seen_at = observation.observed_at

        db.commit()
        db.refresh(observation)
        CatService._add_audit_record(db, cat, "审核通过", "新增观察记录", current_user)
        return _observation_to_dict(observation)

    @staticmethod
    def list_audit_records(db: Session, cat_id: str) -> list[dict]:
        cat = CatService.resolve_cat(db, cat_id)
        records = (
            db.query(CatAuditRecord)
            .filter(CatAuditRecord.cat_id == cat.id)
            .order_by(CatAuditRecord.operated_at.desc())
            .all()
        )
        return [_audit_record_to_dict(record) for record in records]

    @staticmethod
    def batch_mark(db: Session, cat_ids: list[str], mark_type: str, remark: Optional[str], current_user: Optional[User]) -> dict:
        cats = CatService._resolve_many(db, cat_ids)
        for cat in cats:
            cat.mark_type = mark_type
            cat.mark_remark = remark or ""
            CatService._add_audit_record(db, cat, "标记待复查", f"[{mark_type}] {remark or ''}".strip(), current_user, commit=False)
        db.commit()
        return {"success": True, "message": f"已批量标记 {len(cats)} 只猫咪"}

    @staticmethod
    def batch_unmark(db: Session, cat_ids: list[str], current_user: Optional[User]) -> dict:
        cats = CatService._resolve_many(db, cat_ids)
        count = 0
        for cat in cats:
            if cat.mark_type or cat.mark_remark:
                cat.mark_type = None
                cat.mark_remark = None
                count += 1
                CatService._add_audit_record(db, cat, "已归档", "取消标记", current_user, commit=False)
        db.commit()
        return {"success": True, "message": f"已取消 {count} 只猫咪的标记"}

    @staticmethod
    def toggle_focus(db: Session, cat_id: str, is_focus: bool) -> dict:
        cat = CatService.resolve_cat(db, cat_id)
        cat.is_focus = is_focus
        db.commit()
        return {"success": True, "message": f"「{cat.name}」{'已设为关注' if is_focus else '已取消关注'}"}

    @staticmethod
    def batch_toggle_focus(db: Session, cat_ids: list[str], is_focus: bool) -> dict:
        cats = CatService._resolve_many(db, cat_ids)
        for cat in cats:
            cat.is_focus = is_focus
        db.commit()
        return {"success": True, "message": f"{'已关注' if is_focus else '已取消关注'} {len(cats)} 只猫咪"}

    @staticmethod
    def _resolve_many(db: Session, cat_ids: list[str]) -> list[Cat]:
        cats = [CatService.resolve_cat(db, cat_id) for cat_id in cat_ids]
        return cats

    @staticmethod
    def _add_audit_record(
        db: Session,
        cat: Cat,
        action: str,
        remark: str,
        current_user: Optional[User],
        commit: bool = True,
    ) -> None:
        db.add(
            CatAuditRecord(
                cat_id=cat.id,
                action=action,
                remark=remark,
                operator_id=current_user.id if current_user else None,
                operator_name=_operator_name(current_user),
                operated_at=datetime.now(),
            )
        )
        if commit:
            db.commit()


cat_service = CatService()
