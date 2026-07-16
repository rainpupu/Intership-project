"""
猫咪视觉识别服务
职责：传入出现事件图片 → YOLO 检测猫咪 → 裁剪 → 特征提取 → 相似度匹配 → 返回 Top 3 候选猫

模型：models/cat_breeds/best.pt（成员2训练的 YOLO 猫品种检测模型，12 类）
"""
import io
import math
import os
import uuid
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.logger import get_logger
from app.entity.db_models import Encounter, EncounterImage, Cat
from app.storage.minio_client import MinIOClient
from app.utils.image_utils import download_image, crop_region, encode_image_to_bytes

logger = get_logger("vision_service")

# ── 模型路径 ──
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "cat_breeds", "best.pt")


class VisionService:
    """
    视觉识别服务

    完整流程：
        1. 从数据库获取出现事件的图片列表
        2. 调用 YOLO 做目标检测，裁剪猫咪区域并上传到 MinIO
        3. 用品种置信度向量作为特征嵌入 (embedding)
        4. 查询数据库中已有的猫咪档案，做余弦相似度匹配
        5. 多图融合：同一事件多张图的结果综合
        6. 封装返回 Top 3 候选猫
    """

    def __init__(self):
        self._model = None
        self._model_loaded = False
        self._class_names: List[str] = []
        self._num_classes: int = 0
        self._minio: Optional[MinIOClient] = None

    def _ensure_model(self):
        """延迟加载模型（首次调用时加载）"""
        if self._model_loaded:
            return

        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(f"模型文件不存在: {_MODEL_PATH}")

        from ultralytics import YOLO

        self._model = YOLO(_MODEL_PATH)
        self._class_names = list(self._model.names.values())
        self._num_classes = len(self._class_names)
        self._model_loaded = True
        logger.info(f"猫咪识别模型加载成功: {_MODEL_PATH}, 类别数={self._num_classes}, 类别={self._class_names}")

    def _get_minio(self) -> MinIOClient:
        if self._minio is None:
            self._minio = MinIOClient()
        return self._minio

    # ═══════════════════════════════════════════════════════════
    # 核心入口：出现事件分析
    # ═══════════════════════════════════════════════════════════

    async def analyze_encounter(
        self,
        db: Session,
        encounter_id: int,
        conf_threshold: float = 0.25,
    ) -> Dict[str, Any]:
        """
        分析出现事件中的猫咪图片，识别个体身份
        """
        try:
            self._ensure_model()

            encounter = self._get_encounter(db, encounter_id)
            if not encounter:
                return self._build_error(encounter_id, "出现事件不存在")

            images = encounter.images
            if not images:
                return self._build_error(encounter_id, "事件中没有图片")

            total_images = len(images)
            logger.info(f"开始分析出现事件 {encounter_id}，共 {total_images} 张图片")

            all_cropped_urls: List[str] = []
            all_embeddings: List[Dict[str, Any]] = []

            for img_record in images:
                # 第二步：检测 + 裁剪 + 上传
                det_results = await self._detect_and_crop(db, img_record, conf_threshold)
                for det in det_results:
                    all_cropped_urls.append(det["cropped_url"])
                    all_embeddings.append({
                        "cropped_url": det["cropped_url"],
                        "breed": det["breed"],
                        "confidence": det["confidence"],
                        "embedding": det["embedding"],
                    })

            detected_cats = len(all_cropped_urls)

            # 第四步：相似度匹配
            if all_embeddings:
                candidates = await self._match_candidates(db, all_embeddings)
            else:
                candidates = []

            # 第五步：多图融合排序
            top_candidates = self._fuse_and_rank(candidates)

            # 第六步：更新事件状态
            encounter.status = "completed"
            encounter.result_analysis = {
                "total_images": total_images,
                "detected_cats": detected_cats,
                "top_candidates": [c["cat_id"] for c in top_candidates],
            }
            db.commit()

            return {
                "status": "completed",
                "encounter_id": encounter_id,
                "cropped_images": all_cropped_urls,
                "candidates": top_candidates,
                "total_images": total_images,
                "detected_cats": detected_cats,
            }

        except Exception as e:
            logger.error(f"分析出现事件失败: encounter_id={encounter_id}, error={e}", exc_info=True)
            return self._build_error(encounter_id, str(e))

    # ═══════════════════════════════════════════════════════════
    # 第一步：获取事件数据
    # ═══════════════════════════════════════════════════════════

    def _get_encounter(self, db: Session, encounter_id: int) -> Optional[Encounter]:
        return db.query(Encounter).filter(Encounter.id == encounter_id).first()

    # ═══════════════════════════════════════════════════════════
    # 第二步：YOLO 目标检测 + 猫咪裁剪 + MinIO 上传
    # ═══════════════════════════════════════════════════════════

    async def _detect_and_crop(
        self,
        db: Session,
        img_record: EncounterImage,
        conf_threshold: float,
    ) -> List[Dict[str, Any]]:
        """
        对单张图片执行猫咪检测，裁剪出猫咪区域，上传到 MinIO

        Returns:
            [{cropped_url, breed, confidence, embedding, bbox}, ...]
        """
        results = []

        try:
            # # 1. 从 MinIO 下载原始图片（暂未接入，本地测试用 test_predict 方法）
            # image = download_image(img_record.original_url)
            # h, w = image.shape[:2]

            # # 2. 调用 YOLO 检测猫咪
            # preds = self._model.predict(source=image, conf=conf_threshold, verbose=False)

            # if not preds or len(preds[0].boxes) == 0:
            #     logger.info(f"图片 {img_record.id} 未检测到猫咪")
            #     return results

            # boxes = preds[0].boxes
            # for i, box in enumerate(boxes):
            #     bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            #     class_id = int(box.cls[0])
            #     breed = self._class_names[class_id]
            #     confidence = float(box.conf[0])

            #     # 3. 裁剪猫咪区域
            #     cropped = crop_region(image, tuple(bbox), padding=20)
            #     cropped_bytes = encode_image_to_bytes(cropped, format=".jpg")

            #     # 4. 上传到 MinIO
            #     object_name = f"encounters/{img_record.encounter_id}/crops/{uuid.uuid4().hex}.jpg"
            #     minio = self._get_minio()
            #     cropped_url = minio.upload_bytes(object_name, cropped_bytes)

            #     # 5. 品种置信度向量作为 embedding（12 维 one-hot 风格）
            #     embedding = [0.0] * self._num_classes
            #     embedding[class_id] = confidence

            #     results.append({
            #         "cropped_url": cropped_url,
            #         "breed": breed,
            #         "confidence": confidence,
            #         "embedding": embedding,
            #         "bbox": bbox,
            #     })

            #     # 6. 更新数据库记录
            #     img_record.bbox = bbox
            #     if i == 0:
            #         img_record.cropped_url = cropped_url
            #     img_record.embedding = embedding

            # db.commit()
            # logger.info(f"图片 {img_record.id} 检测到 {len(results)} 只猫咪: {[r['breed'] for r in results]}")

            # TODO: 数据库就绪后取消注释以上代码
            logger.warning("_detect_and_crop: 数据库/MinIO 暂未接入，请使用 test_predict() 方法测试模型")

        except Exception as e:
            logger.error(f"检测图片失败: img_id={img_record.id}, error={e}", exc_info=True)

        return results

    # ═══════════════════════════════════════════════════════════
    # 第三步：特征提取（由 YOLO 品种置信度向量充当 embedding）
    # ═══════════════════════════════════════════════════════════

    # embedding 已在 _detect_and_crop 中直接生成，此方法保留用于将来独立特征提取模型的接入
    async def _extract_embedding(self, cropped_image_url: str) -> Optional[List[float]]:
        """
        对裁剪后的猫咪图片提取特征向量（预留接口）

        当前方案：YOLO 检测时已产出 12 维品种置信度向量作为 embedding，
        因此此方法暂不单独调用。将来接入独立特征提取模型时在此实现。
        """
        pass

    # ═══════════════════════════════════════════════════════════
    # 第四步：相似度匹配
    # ═══════════════════════════════════════════════════════════

    async def _match_candidates(
        self,
        db: Session,
        embeddings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        用检测到的品种特征向量与数据库中已有的猫咪档案做匹配

        策略：
        1. 从数据库获取所有猫咪档案
        2. 对每个检测到的猫咪，计算与所有档案的余弦相似度
        3. 返回所有匹配结果（含相似度）

        TODO: 数据库就绪后取消注释
        """
        # cats = db.query(Cat).filter(Cat.status == "active").all()
        # if not cats:
        #     logger.info("数据库中没有猫咪档案，无法匹配")
        #     return []
        #
        # candidates = []
        # for emb_info in embeddings:
        #     query_vec = emb_info["embedding"]
        #     query_breed = emb_info["breed"]
        #     query_conf = emb_info["confidence"]
        #
        #     for cat in cats:
        #         cat_vec = cat.embedding
        #         if cat_vec and len(cat_vec) == self._num_classes:
        #             similarity = self._cosine_similarity(query_vec, cat_vec)
        #         else:
        #             similarity = self._breed_match_score(query_breed, cat)
        #
        #         if similarity > 0:
        #             candidates.append({
        #                 "cat_id": cat.id,
        #                 "name": cat.name,
        #                 "similarity": round(similarity, 4),
        #                 "ref_image_url": cat.ref_image_url or "",
        #                 "breed": query_breed,
        #                 "breed_confidence": query_conf,
        #             })
        #
        # return candidates

        logger.warning("_match_candidates: 数据库暂未接入，返回空列表")
        return []

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _breed_match_score(self, breed: str, cat: Cat) -> float:
        """基于品种名称的模糊匹配得分（兜底方案）"""
        breed_lower = breed.lower()
        color = (cat.color or "").lower()
        description = (cat.description or "").lower()

        # 品种名直接在毛色/描述中出现
        if breed_lower in color or breed_lower in description:
            return 0.75
        # 部分匹配
        parts = breed_lower.split("_")
        for part in parts:
            if part in color or part in description:
                return 0.60
        return 0.0

    # ═══════════════════════════════════════════════════════════
    # 第五步：多图融合
    # ═══════════════════════════════════════════════════════════

    def _fuse_and_rank(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        多图融合：同一事件多张图的结果综合排序

        策略：
        1. 按 cat_id 聚合，取最高相似度作为该猫的得分
        2. 按相似度降序排列
        3. 返回 Top 3
        """
        best: Dict[int, Dict[str, Any]] = {}
        for c in candidates:
            cid = c["cat_id"]
            if cid not in best or c["similarity"] > best[cid]["similarity"]:
                best[cid] = c

        ranked = sorted(best.values(), key=lambda x: x["similarity"], reverse=True)
        return ranked[:3]

    # ═══════════════════════════════════════════════════════════
    # 测试方法：本地图片直接预测（无数据库依赖）
    # ═══════════════════════════════════════════════════════════

    def test_predict(self, image_path: str = "test_cat.jpg", device: str = "cpu"):
        """
        本地图片测试预测，不依赖数据库和 MinIO

        执行完整流程：检测 → 裁剪 → 保存本地裁剪图 → 返回结果

        Args:
            image_path: 本地图片路径
            device: 推理设备（cpu / cuda:0）

        Returns:
            {
                "status": "completed" | "failed",
                "encounter_id": int,
                "cropped_images": [str, ...],      # 裁剪图本地 URL
                "candidates": [CandidateCat, ...],  # 检测到的猫咪列表
                "total_images": int,
                "detected_cats": int,
            }
        """
        self._ensure_model()

        print(f"\n{'='*60}")
        print(f"测试图片: {image_path}")
        print(f"设备: {device}")
        print(f"{'='*60}")

        # 1. 执行模型推理
        results = self._model.predict(source=image_path, device=device, verbose=True)
        result = results[0]  # 单图取第一个结果

        cropped_urls = []
        candidates = []

        # 2. 如果检测到了猫咪
        if len(result.boxes) > 0:
            # 读取原图用于裁剪
            orig_img = cv2.imread(image_path)
            if orig_img is None:
                print(f"错误: 无法读取图片 {image_path}")
                return self._build_test_error(0, "无法读取图片")

            # 确保 static 目录存在
            static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static")
            os.makedirs(static_dir, exist_ok=True)

            # 原始图像尺寸
            ori_h, ori_w = result.orig_shape

            for i, box in enumerate(result.boxes):
                # 提取核心数据
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = result.names[cls_id]

                # 模型原始输出（浮点数，与 YOLO 直接预测一致）
                raw_xyxy = box.xyxy[0].tolist()          # [x1, y1, x2, y2] 浮点
                raw_xywh = box.xywh[0].tolist()          # [cx, cy, w, h] 浮点
                raw_xyxyn = box.xyxyn[0].tolist()        # [x1, y1, x2, y2] 归一化 0~1

                # 裁剪用整数坐标（必须 int 才能切片）
                x1, y1, x2, y2 = int(raw_xyxy[0]), int(raw_xyxy[1]), int(raw_xyxy[2]), int(raw_xyxy[3])

                print(f"\n检测到 #{i+1}: {class_name}")
                print(f"  原始图像尺寸: {ori_w}x{ori_h}")
                print(f"  模型原始 xyxy: [{raw_xyxy[0]:.2f}, {raw_xyxy[1]:.2f}, {raw_xyxy[2]:.2f}, {raw_xyxy[3]:.2f}]")
                print(f"  模型原始 xywh: [{raw_xywh[0]:.2f}, {raw_xywh[1]:.2f}, {raw_xywh[2]:.2f}, {raw_xywh[3]:.2f}]")
                print(f"  归一化坐标 xyxyn: [{raw_xyxyn[0]:.4f}, {raw_xyxyn[1]:.4f}, {raw_xyxyn[2]:.4f}, {raw_xyxyn[3]:.4f}]")
                print(f"  置信度: {conf:.2%}")
                print(f"  裁剪坐标(整数): ({x1}, {y1}) → ({x2}, {y2})")
                print(f"  裁剪尺寸: {x2-x1} x {y2-y1} px")

                # 3. 图像裁剪（根据坐标剪下猫咪小图）
                cropped_img = orig_img[y1:y2, x1:x2]

                # 4. 保存裁剪图到本地 static 目录
                crop_filename = f"crop_{i+1}_{class_name}.jpg"
                crop_path = os.path.join(static_dir, crop_filename)
                cv2.imwrite(crop_path, cropped_img)
                print(f"  裁剪图已保存: static/{crop_filename}")

                # 本地静态文件 URL
                crop_url = f"http://localhost:8888/static/{crop_filename}"
                cropped_urls.append(crop_url)

                # 5. 组装候选猫咪信息（保留浮点精度）
                candidates.append({
                    "cat_id": cls_id + 1,
                    "name": class_name,
                    "similarity": conf,
                    "ref_image_url": crop_url,
                    # 返回模型原始浮点坐标，与 YOLO 直接预测一致
                    "bbox": {
                        "xyxy": [round(v, 2) for v in raw_xyxy],
                        "xywh": [round(v, 2) for v in raw_xywh],
                        "xyxyn": [round(v, 4) for v in raw_xyxyn],
                    },
                    "image_size": {"width": ori_w, "height": ori_h},
                })
        else:
            print("未检测到猫咪")

        print(f"\n{'='*60}")
        print(f"检测结果: {len(candidates)} 只猫咪, {len(cropped_urls)} 张裁剪图")
        print(f"{'='*60}\n")

        return {
            "status": "completed" if len(candidates) > 0 else "failed",
            "encounter_id": 0,
            "cropped_images": cropped_urls,
            "candidates": candidates,
            "total_images": 1,
            "detected_cats": len(candidates),
        }

    def _build_test_error(self, encounter_id: int, message: str) -> Dict[str, Any]:
        return {
            "status": "failed",
            "encounter_id": encounter_id,
            "cropped_images": [],
            "candidates": [],
            "total_images": 0,
            "detected_cats": 0,
            "error": message,
        }

    # ═══════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════

    def _build_error(self, encounter_id: int, message: str) -> Dict[str, Any]:
        return {
            "status": "failed",
            "encounter_id": encounter_id,
            "cropped_images": [],
            "candidates": [],
            "total_images": 0,
            "detected_cats": 0,
            "error": message,
        }


# ── 全局单例 ──
vision_service = VisionService()