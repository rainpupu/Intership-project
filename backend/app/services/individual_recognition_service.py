from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.entity.db_models import Cat, CatIdentityEmbedding, CatObservation, RecognitionRecord, User


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "individual" / "best_model.pth"


class CatIndividualModelDefinition:
    @staticmethod
    def build(embedding_dim: int = 512):
        import torch.nn as nn
        import torch.nn.functional as F
        import torchvision.models as models

        class CatIndividualModel(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                backbone = models.resnet50(weights=None)
                self.backbone = nn.Sequential(*list(backbone.children())[:-2])
                self.avgpool = nn.AdaptiveAvgPool2d(1)
                self.bn1 = nn.BatchNorm1d(2048)
                self.dropout = nn.Dropout(0.3)
                self.fc = nn.Linear(2048, embedding_dim)
                self.bn2 = nn.BatchNorm1d(embedding_dim)

            def forward(self, x):
                x = self.backbone(x)
                x = self.avgpool(x).view(x.size(0), -1)
                x = self.bn1(x)
                x = self.dropout(x)
                x = self.bn2(self.fc(x))
                return F.normalize(x)

        return CatIndividualModel()


def _external_cat_id(cat: Cat) -> str:
    return cat.code or str(cat.id)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, dot / (norm_a * norm_b))


class IndividualRecognitionService:
    def __init__(self) -> None:
        self._model = None
        self._transform = None
        self._device = "cpu"
        self._load_error: str | None = None

    def is_available(self) -> bool:
        return MODEL_PATH.exists() and self._load_error is None

    def identify_crop(self, db: Session, crop_path: Path, breed_name: str | None = None, top_k: int = 3) -> dict[str, Any]:
        if not MODEL_PATH.exists():
            return {"available": False, "matches": [], "embedding": None, "message": "个体识别模型文件不存在"}

        try:
            embedding = self.extract_embedding(crop_path)
        except Exception as exc:  # pragma: no cover - runtime model failures are environment-specific
            self._load_error = str(exc)
            return {"available": False, "matches": [], "embedding": None, "message": str(exc)}

        matches = self.find_matches(db, embedding, breed_name=breed_name, top_k=top_k)
        return {
            "available": True,
            "matches": matches,
            "embedding": embedding,
            "message": self._build_match_message(breed_name, bool(matches)),
        }

    def extract_embedding(self, image_path: Path) -> list[float]:
        self._ensure_model()

        from PIL import Image
        import torch

        image = Image.open(image_path).convert("RGB")
        tensor = self._transform(image).unsqueeze(0).to(self._device)
        with torch.no_grad():
            embedding = self._model(tensor).squeeze(0).cpu().tolist()
        return [round(float(value), 8) for value in embedding]

    def find_matches(
        self,
        db: Session,
        embedding: list[float],
        breed_name: str | None = None,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        query = db.query(CatIdentityEmbedding).join(Cat)
        if breed_name:
            query = query.filter(Cat.coat_color == breed_name)
        references = query.all()
        candidates: list[dict[str, Any]] = []
        for reference in references:
            ref_embedding = reference.embedding or []
            if len(ref_embedding) != len(embedding):
                continue

            similarity = _cosine_similarity(embedding, [float(value) for value in ref_embedding])
            candidates.append(
                {
                    "catId": _external_cat_id(reference.cat),
                    "name": reference.cat.name,
                    "image": reference.image_url or reference.cat.cover_image or "",
                    "similarity": round(similarity, 4),
                    "breedName": reference.cat.coat_color,
                }
            )

        candidates.sort(key=lambda item: item["similarity"], reverse=True)
        return candidates[:top_k]

    def _build_match_message(self, breed_name: str | None, has_matches: bool) -> str:
        if has_matches:
            return f"已限定在「{breed_name}」品种参考库内完成个体匹配" if breed_name else "个体识别模型已提取特征"
        if breed_name:
            return f"已限定在「{breed_name}」品种参考库内匹配，暂无可用参考特征"
        return "个体识别模型已提取特征，暂无可匹配的猫咪参考特征"

    def attach_record_to_cat(self, db: Session, record_id: str, cat_id: str, current_user: User) -> dict:
        record_pk = self._parse_record_id(record_id)
        record = db.query(RecognitionRecord).filter(RecognitionRecord.id == record_pk).first()
        if not record:
            raise HTTPException(status_code=404, detail="识别记录不存在")
        if record.user_id != current_user.id and current_user.role not in ("admin", "super_admin"):
            raise HTTPException(status_code=403, detail="不能修改其他账号的识别记录")

        cat = self._resolve_cat(db, cat_id)
        candidate = self._first_candidate_with_embedding(record)
        embedding = candidate.get("identityEmbedding")
        if not embedding:
            raise HTTPException(status_code=400, detail="该识别记录没有可登记的个体特征")

        image_url = candidate.get("cropImage") or candidate.get("image") or record.image
        self._apply_status_observation(
            db,
            cat,
            record,
            candidate,
            current_user,
            location=self._record_location_for_observation(record),
        )
        db.add(
            CatIdentityEmbedding(
                cat_id=cat.id,
                embedding=embedding,
                image_url=image_url,
                source="confirmed_recognition",
                created_by_id=current_user.id,
            )
        )
        record.cat_id = _external_cat_id(cat)
        record.cat_name = cat.name
        record.status = "已确认"
        db.commit()
        return {"success": True, "catId": _external_cat_id(cat), "message": "个体特征已登记到猫咪档案"}

    def create_cat_from_record(self, db: Session, record_id: str, payload: dict[str, Any], current_user: User) -> dict:
        if current_user.role not in ("admin", "super_admin"):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        record_pk = self._parse_record_id(record_id)
        record = db.query(RecognitionRecord).filter(RecognitionRecord.id == record_pk).first()
        if not record:
            raise HTTPException(status_code=404, detail="识别记录不存在")

        candidate = self._first_candidate_with_embedding(record)
        embedding = candidate.get("identityEmbedding")
        if not embedding:
            raise HTTPException(status_code=400, detail="该识别记录没有可登记的个体特征")

        code = (payload.get("code") or "").strip() or self._generate_cat_code(db)
        if db.query(Cat).filter(Cat.code == code).first():
            raise HTTPException(status_code=409, detail="猫咪编号已存在")

        image_url = candidate.get("cropImage") or candidate.get("image") or record.image
        breed_name = candidate.get("breedName") or "未知品种"
        health_status = candidate.get("healthStatus") or record.health_status
        mood_status = candidate.get("moodStatus") or record.mood_status
        observed_at = record.observed_at or record.created_at or datetime.now()
        last_seen_location = (payload.get("last_seen_location") or "").strip() or self._record_location_for_observation(record)
        similarity = float(candidate.get("similarity") or record.similarity or 0)
        auto_name = self._build_default_name(db)
        name = (payload.get("name") or "").strip() or auto_name
        description = (payload.get("description") or "").strip() or self._build_auto_description(
            breed_name=breed_name,
            similarity=similarity,
            source_status=record.status,
        )
        cat = Cat(
            code=code,
            name=name,
            cover_image=image_url,
            gallery_images=[image_url] if image_url else [],
            coat_color=breed_name,
            health_status=health_status,
            mood_status=mood_status,
            adoption_status="暂不开放",
            last_seen_location=last_seen_location,
            last_seen_at=observed_at,
            description=description,
            created_by_id=current_user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(cat)
        db.flush()

        db.add(
            CatIdentityEmbedding(
                cat_id=cat.id,
                embedding=embedding,
                image_url=image_url,
                source="new_cat_recognition",
                created_by_id=current_user.id,
            )
        )
        db.add(
            CatObservation(
                cat_id=cat.id,
                location=last_seen_location,
                mood_status=mood_status,
                health_status=health_status,
                observed_at=observed_at,
                description=self._build_observation_description(record),
                created_by_id=current_user.id,
            )
        )
        record.cat_id = _external_cat_id(cat)
        record.cat_name = cat.name
        record.status = "已建档"
        db.commit()
        db.refresh(cat)

        return {
            "success": True,
            "catId": _external_cat_id(cat),
            "name": cat.name,
            "message": "新猫档案已创建，个体特征已登记",
        }

    def _ensure_model(self) -> None:
        if self._model is not None:
            return

        import torch
        import torchvision.transforms as transforms

        checkpoint = torch.load(MODEL_PATH, map_location=self._device)
        embedding_dim = int(checkpoint.get("embedding_dim", 512))
        model = CatIndividualModelDefinition.build(embedding_dim=embedding_dim)
        model.load_state_dict(checkpoint["model_state_dict"], strict=False)
        model.to(self._device)
        model.eval()

        self._model = model
        self._transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )

    def _resolve_cat(self, db: Session, cat_id: str) -> Cat:
        query = db.query(Cat)
        if cat_id.isdigit():
            cat = query.filter(or_(Cat.id == int(cat_id), Cat.code == cat_id)).first()
        else:
            cat = query.filter(Cat.code == cat_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="猫咪档案不存在")
        return cat

    def _parse_record_id(self, record_id: str) -> int:
        raw = record_id.removeprefix("rec-")
        if not raw.isdigit():
            raise HTTPException(status_code=400, detail="识别记录编号无效")
        return int(raw)

    def _first_candidate_with_embedding(self, record: RecognitionRecord) -> dict[str, Any]:
        for candidate in record.candidates or []:
            if candidate.get("identityEmbedding"):
                return candidate
        return {}

    def _apply_status_observation(
        self,
        db: Session,
        cat: Cat,
        record: RecognitionRecord,
        candidate: dict[str, Any],
        current_user: User,
        location: str | None,
    ) -> None:
        health_status = candidate.get("healthStatus") or record.health_status
        mood_status = candidate.get("moodStatus") or record.mood_status
        observed_at = record.observed_at or record.created_at or datetime.now()

        if health_status:
            cat.health_status = health_status
        if mood_status:
            cat.mood_status = mood_status
        if location:
            cat.last_seen_location = location
        cat.last_seen_at = observed_at

        if health_status or mood_status or location:
            db.add(
                CatObservation(
                    cat_id=cat.id,
                    location=location,
                    mood_status=mood_status,
                    health_status=health_status,
                    observed_at=observed_at,
                    description=self._build_observation_description(record),
                    created_by_id=current_user.id,
                )
            )

    def _record_location_for_observation(self, record: RecognitionRecord) -> str | None:
        if record.location and record.location != "用户上传":
            return record.location
        return None

    def _build_observation_description(self, record: RecognitionRecord) -> str:
        parts = ["由识别流程补充健康和心情信息。"]
        if record.status == "线索待审核":
            parts.append("该记录来自用户提交的校园猫线索，已由管理员确认。")
        if record.user_remark:
            parts.append(f"用户备注：{record.user_remark}")
        return "".join(parts)

    def _generate_cat_code(self, db: Session) -> str:
        prefix = datetime.now().strftime("cat-%Y%m%d%H%M%S")
        code = prefix
        suffix = 1
        while db.query(Cat).filter(Cat.code == code).first():
            suffix += 1
            code = f"{prefix}-{suffix}"
        return code

    def _build_default_name(self, db: Session) -> str:
        prefix = datetime.now().strftime("待命名猫咪-%m%d%H%M")
        name = prefix
        suffix = 1
        while db.query(Cat).filter(Cat.name == name).first():
            suffix += 1
            name = f"{prefix}-{suffix}"
        return name

    def _build_auto_description(self, breed_name: str, similarity: float, source_status: str | None) -> str:
        parts = [
            "由识别结果自动创建的待完善猫咪档案。",
            f"YOLO 品种候选：{breed_name}。",
        ]
        if similarity:
            parts.append(f"本次候选置信度：{similarity:.1%}。")
        if source_status:
            parts.append(f"识别状态：{source_status}。")
        parts.append("管理员可后续补充昵称、年龄、性格、健康和领养状态等信息。")
        return "".join(parts)


individual_recognition_service = IndividualRecognitionService()
