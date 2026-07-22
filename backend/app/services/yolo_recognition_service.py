from __future__ import annotations

import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

import cv2
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.services.breed_name_service import to_chinese_breed_name
from app.services.individual_recognition_service import individual_recognition_service


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "cat_breeds" / "best.pt"
HEALTH_MODEL_PATH = BASE_DIR / "models" / "health" / "best.pt"
EMOTION_MODEL_PATH = BASE_DIR / "models" / "emotion" / "best.pt"
STATIC_DIR = BASE_DIR / "static" / "recognition"
UPLOAD_DIR = STATIC_DIR / "uploads"
CROP_DIR = STATIC_DIR / "crops"
ANNOTATED_DIR = STATIC_DIR / "annotated"
CACHE_DIR = BASE_DIR / ".runtime_cache"
IDENTITY_MATCH_THRESHOLD = 0.50

for directory in (UPLOAD_DIR, CROP_DIR, ANNOTATED_DIR, CACHE_DIR / "ultralytics", CACHE_DIR / "torch"):
    directory.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("ULTRALYTICS_CACHE_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("TORCH_HOME", str(CACHE_DIR / "torch"))


class YoloRecognitionService:
    def __init__(self) -> None:
        self._model = None
        self._health_model = None
        self._emotion_model = None
        self._class_names: dict[int, str] = {}
        self._health_class_names: dict[int, str] = {}
        self._emotion_class_names: dict[int, str] = {}

    def _ensure_model(self):
        if self._model is not None:
            return self._model

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"YOLO model not found: {MODEL_PATH}")

        from ultralytics import YOLO

        self._model = YOLO(str(MODEL_PATH))
        self._class_names = dict(self._model.names)
        return self._model

    def _ensure_health_model(self):
        if self._health_model is not None:
            return self._health_model
        if not HEALTH_MODEL_PATH.exists():
            return None

        from ultralytics import YOLO

        self._health_model = YOLO(str(HEALTH_MODEL_PATH))
        self._health_class_names = dict(self._health_model.names)
        return self._health_model

    def _ensure_emotion_model(self):
        if self._emotion_model is not None:
            return self._emotion_model
        if not EMOTION_MODEL_PATH.exists():
            return None

        from ultralytics import YOLO

        self._emotion_model = YOLO(str(EMOTION_MODEL_PATH))
        self._emotion_class_names = dict(self._emotion_model.names)
        return self._emotion_model

    async def analyze_uploads(
        self,
        files: list[UploadFile],
        base_url: str,
        conf_threshold: float = 0.25,
        db: Session | None = None,
    ) -> dict[str, Any]:
        model = self._ensure_model()
        started_at = time.perf_counter()
        detections: list[dict[str, Any]] = []
        uploaded_images: list[str] = []

        for file in files:
            image_path = await self._save_upload(file)
            uploaded_images.append(self._to_url(base_url, image_path))

            result = model.predict(source=str(image_path), conf=conf_threshold, verbose=False)[0]
            original = cv2.imread(str(image_path))
            if original is None:
                continue

            boxes = result.boxes if result.boxes is not None else []
            image_detections: list[dict[str, Any]] = []
            for index, box in enumerate(boxes):
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                xyxy = [float(value) for value in box.xyxy[0].tolist()]
                crop_path = self._save_crop(original, xyxy, image_path.stem, index)
                raw_breed_name = self._class_names.get(class_id, f"class_{class_id}")
                breed_name = to_chinese_breed_name(raw_breed_name)

                detection = self._build_breed_detection(
                    class_id=class_id,
                    breed_name=breed_name,
                    confidence=confidence,
                    bbox=xyxy,
                    crop_url=self._to_url(base_url, crop_path),
                )

                identity = (
                    individual_recognition_service.identify_crop(db, crop_path, breed_name=breed_name)
                    if db is not None
                    else {"available": False, "matches": [], "embedding": None, "message": "未连接数据库，跳过个体匹配"}
                )
                if identity.get("embedding"):
                    detection["identityEmbedding"] = identity["embedding"]
                    detection["identityStatus"] = identity.get("message")

                best_match = identity["matches"][0] if identity.get("matches") else None
                match = best_match if best_match and best_match["similarity"] >= IDENTITY_MATCH_THRESHOLD else None
                if match:
                    detection.update(
                        {
                            "catId": match["catId"],
                            "name": match["name"],
                            "similarity": match["similarity"],
                            "reason": self._build_identity_reason(match["similarity"], breed_name, confidence),
                            "status": "个体识别匹配结果",
                            "modelType": "individual",
                            "matchedImage": match.get("image", ""),
                        }
                    )
                elif identity.get("embedding"):
                    detection.update(
                        {
                            "status": "疑似新猫，待管理员确认",
                            "modelType": "new",
                            "identityStatus": identity.get("message"),
                        }
                    )

                self._apply_post_identity_models(detection, crop_path)

                image_detections.append(detection)

            if image_detections:
                annotated_path = self._save_annotated(original, image_detections, image_path.stem)
                annotated_url = self._to_url(base_url, annotated_path)
                for detection in image_detections:
                    detection["image"] = annotated_url
                    detections.append(detection)

        detections.sort(key=lambda item: item["similarity"], reverse=True)
        top_candidates = detections[:3]
        best_confidence = top_candidates[0]["similarity"] if top_candidates else 0
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

        return {
            "candidates": top_candidates,
            "analysis": {
                "confidence": best_confidence,
                "healthHints": self._build_health_hints(top_candidates),
                "behaviorHints": self._build_behavior_hints(top_candidates),
                "summary": self._build_summary(len(files), len(detections), elapsed_ms),
            },
            "uploadedImages": uploaded_images,
            "detectedCount": len(detections),
            "elapsedMs": elapsed_ms,
        }

    async def _save_upload(self, file: UploadFile) -> Path:
        suffix = Path(file.filename or "").suffix.lower() or ".jpg"
        if suffix not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            suffix = ".jpg"

        target = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
        with target.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return target

    def _save_crop(self, image, bbox: list[float], source_stem: str, index: int) -> Path:
        height, width = image.shape[:2]
        x1, y1, x2, y2 = [int(value) for value in bbox]
        x1 = max(0, min(width, x1))
        x2 = max(0, min(width, x2))
        y1 = max(0, min(height, y1))
        y2 = max(0, min(height, y2))

        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            crop = image

        crop_path = CROP_DIR / f"{source_stem}_{index + 1}.jpg"
        cv2.imwrite(str(crop_path), crop)
        return crop_path

    def _save_annotated(self, image, detections: list[dict[str, Any]], source_stem: str) -> Path:
        annotated = image.copy()
        height, width = annotated.shape[:2]
        line_width = max(2, round((height + width) / 650))
        font_scale = max(0.55, min(0.9, line_width * 0.28))

        for detection in detections:
            x1, y1, x2, y2 = [int(value) for value in detection["bbox"]]
            x1 = max(0, min(width - 1, x1))
            x2 = max(0, min(width - 1, x2))
            y1 = max(0, min(height - 1, y1))
            y2 = max(0, min(height - 1, y2))

            color = (94, 197, 34)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, line_width)

            label = detection["name"]
            (label_width, label_height), baseline = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                line_width,
            )
            label_y = max(label_height + baseline + 6, y1)
            cv2.rectangle(
                annotated,
                (x1, label_y - label_height - baseline - 6),
                (min(width - 1, x1 + label_width + 8), label_y),
                color,
                -1,
            )
            cv2.putText(
                annotated,
                label,
                (x1 + 4, label_y - baseline - 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                max(1, line_width - 1),
                cv2.LINE_AA,
            )

        annotated_path = ANNOTATED_DIR / f"{source_stem}_annotated.jpg"
        cv2.imwrite(str(annotated_path), annotated)
        return annotated_path

    def _build_breed_detection(
        self,
        class_id: int,
        breed_name: str,
        confidence: float,
        bbox: list[float],
        crop_url: str,
    ) -> dict[str, Any]:
        return {
            "catId": f"breed-{class_id}",
            "name": breed_name,
            "image": "",
            "cropImage": crop_url,
            "similarity": round(confidence, 4),
            "reason": self._build_reason(confidence, bbox),
            "status": "YOLO 品种识别结果",
            "bbox": [round(value, 2) for value in bbox],
            "modelType": "breed",
            "breedName": breed_name,
            "breedConfidence": round(confidence, 4),
        }

    def _apply_post_identity_models(self, detection: dict[str, Any], crop_path: Path) -> None:
        health = self._predict_best_label(
            model=self._ensure_health_model(),
            class_names=self._health_class_names,
            image_path=crop_path,
        )
        emotion = self._predict_best_label(
            model=self._ensure_emotion_model(),
            class_names=self._emotion_class_names,
            image_path=crop_path,
        )

        if health:
            detection["healthStatus"] = self._map_health_label(health["label"])
            detection["healthConfidence"] = health["confidence"]
        if emotion:
            detection["moodStatus"] = self._map_emotion_label(emotion["label"])
            detection["moodConfidence"] = emotion["confidence"]

    def _predict_best_label(self, model, class_names: dict[int, str], image_path: Path) -> dict[str, Any] | None:
        if model is None:
            return None
        try:
            result = model.predict(source=str(image_path), verbose=False)[0]
        except Exception:
            return None

        best_label: str | None = None
        best_confidence = 0.0
        boxes = result.boxes if result.boxes is not None else []
        for box in boxes:
            confidence = float(box.conf[0])
            if confidence > best_confidence:
                class_id = int(box.cls[0])
                best_label = class_names.get(class_id, f"class_{class_id}")
                best_confidence = confidence

        probs = getattr(result, "probs", None)
        if best_label is None and probs is not None and getattr(probs, "top1", None) is not None:
            class_id = int(probs.top1)
            best_label = class_names.get(class_id, f"class_{class_id}")
            best_confidence = float(probs.top1conf)

        if best_label is None:
            return None
        return {"label": best_label, "confidence": round(best_confidence, 4)}

    def _map_health_label(self, label: str) -> str:
        return {
            "Healthy": "健康良好",
            "Sick": "需复查",
        }.get(label, label)

    def _map_emotion_label(self, label: str) -> str:
        return {
            "Anger": "生气",
            "Beg": "讨食",
            "Frightened": "紧张",
            "Happy": "开心",
            "Scare": "受惊",
            "Sleepy": "困倦",
            "Wonder": "好奇",
        }.get(label, label)

    def _build_health_hints(self, candidates: list[dict[str, Any]]) -> list[str]:
        statuses = [candidate.get("healthStatus") for candidate in candidates if candidate.get("healthStatus")]
        if statuses:
            return [f"健康模型判断：{status}" for status in statuses[:3]]
        return ["健康模型未输出明确结论，请结合人工观察补充。"]

    def _build_behavior_hints(self, candidates: list[dict[str, Any]]) -> list[str]:
        statuses = [candidate.get("moodStatus") for candidate in candidates if candidate.get("moodStatus")]
        if statuses:
            return [f"心情模型判断：{status}" for status in statuses[:3]]
        return ["心情模型未输出明确结论，请结合现场行为补充。"]

    def _to_url(self, base_url: str, path: Path) -> str:
        relative = path.relative_to(BASE_DIR / "static").as_posix()
        return f"{base_url.rstrip('/')}/static/{relative}"

    def _build_reason(self, confidence: float, bbox: list[float]) -> str:
        x1, y1, x2, y2 = bbox
        width = max(0, x2 - x1)
        height = max(0, y2 - y1)
        return f"YOLO 已检测到猫咪目标，目标框约 {width:.0f}x{height:.0f}px。"

    def _build_identity_reason(self, similarity: float, breed_name: str, breed_confidence: float) -> str:
        return f"个体识别已匹配已有档案；YOLO 品种候选为 {breed_name}。"

    def _build_summary(self, image_count: int, detection_count: int, elapsed_ms: float) -> str:
        if detection_count == 0:
            return f"已处理 {image_count} 张图片，暂未检测到猫咪目标。请尝试上传更清晰、主体更完整的猫咪照片。"

        return f"已处理 {image_count} 张图片，检测到 {detection_count} 个猫咪目标，用时约 {elapsed_ms:.0f}ms。当前结果来自 YOLO 检测和 ResNet50 + ArcFace 个体特征模型。"


yolo_recognition_service = YoloRecognitionService()
