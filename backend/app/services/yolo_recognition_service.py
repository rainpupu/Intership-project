from __future__ import annotations

import shutil
import time
import uuid
import os
from pathlib import Path
from typing import Any

import cv2
from fastapi import UploadFile


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "cat_breeds" / "best.pt"
STATIC_DIR = BASE_DIR / "static" / "recognition"
UPLOAD_DIR = STATIC_DIR / "uploads"
CROP_DIR = STATIC_DIR / "crops"
ANNOTATED_DIR = STATIC_DIR / "annotated"
CACHE_DIR = BASE_DIR / ".runtime_cache"

for directory in (UPLOAD_DIR, CROP_DIR, ANNOTATED_DIR, CACHE_DIR / "ultralytics", CACHE_DIR / "torch"):
    directory.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("ULTRALYTICS_CACHE_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("TORCH_HOME", str(CACHE_DIR / "torch"))


class YoloRecognitionService:
    def __init__(self) -> None:
        self._model = None
        self._class_names: dict[int, str] = {}

    def _ensure_model(self):
        if self._model is not None:
            return self._model

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"YOLO model not found: {MODEL_PATH}")

        from ultralytics import YOLO

        self._model = YOLO(str(MODEL_PATH))
        self._class_names = dict(self._model.names)
        return self._model

    async def analyze_uploads(self, files: list[UploadFile], base_url: str, conf_threshold: float = 0.25) -> dict[str, Any]:
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

                image_detections.append(
                    {
                        "catId": f"breed-{class_id}",
                        "name": self._class_names.get(class_id, f"class_{class_id}"),
                        "image": "",
                        "cropImage": self._to_url(base_url, crop_path),
                        "similarity": round(confidence, 4),
                        "reason": self._build_reason(confidence, xyxy),
                        "status": "YOLO 品种识别结果",
                        "bbox": [round(value, 2) for value in xyxy],
                    }
                )

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
                "healthHints": ["当前模型仅做猫咪品种与目标框识别，暂不判断健康状态。"],
                "behaviorHints": ["未接入行为识别模型，姿态和情绪分析暂不输出结论。"],
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

            label = f"{detection['name']} {detection['similarity']:.0%}"
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

    def _to_url(self, base_url: str, path: Path) -> str:
        relative = path.relative_to(BASE_DIR / "static").as_posix()
        return f"{base_url.rstrip('/')}/static/{relative}"

    def _build_reason(self, confidence: float, bbox: list[float]) -> str:
        x1, y1, x2, y2 = bbox
        width = max(0, x2 - x1)
        height = max(0, y2 - y1)
        return f"YOLO 检测置信度 {confidence:.1%}，目标框约 {width:.0f}×{height:.0f}px。"

    def _build_summary(self, image_count: int, detection_count: int, elapsed_ms: float) -> str:
        if detection_count == 0:
            return f"已处理 {image_count} 张图片，暂未检测到猫咪目标。请尝试上传更清晰、主体更完整的猫咪照片。"

        return f"已处理 {image_count} 张图片，检测到 {detection_count} 个猫咪目标，用时约 {elapsed_ms:.0f}ms。当前结果来自本地 YOLO 模型，未接入数据库身份匹配。"


yolo_recognition_service = YoloRecognitionService()
