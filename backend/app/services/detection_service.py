"""
检测服务模块
提供 YOLOv11 目标检测的完整业务逻辑
包括单图检测、批量检测、文件夹检测、视频检测等
"""
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.logger import get_logger
from app.entity.db_models import (
    DetectionTask, DetectionResult, DetectionScene, ModelVersion
)
from app.storage.minio_client import MinIOClient

logger = get_logger("detection_service")


class DetectionService:
    """检测服务类"""
    
    def __init__(self):
        self.models: Dict[int, Any] = {}  # scene_id -> YOLO model
        self.minio_client = None
    
    def load_model(self, scene_id: int, model_path: str) -> bool:
        """
        加载场景对应的模型
        
        Args:
            scene_id: 场景ID
            model_path: 模型文件路径
        
        Returns:
            是否加载成功
        """
        try:
            from ultralytics import YOLO
            
            if not os.path.exists(model_path):
                logger.error(f"模型文件不存在: {model_path}")
                return False
            
            self.models[scene_id] = YOLO(model_path)
            logger.info(f"加载模型成功: scene_id={scene_id}, path={model_path}")
            return True
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    def get_default_model_path(self, db: Session, scene_id: int) -> Optional[str]:
        """
        获取场景的默认模型路径
        
        Args:
            db: 数据库会话
            scene_id: 场景ID
        
        Returns:
            模型路径
        """
        # 查找默认模型版本
        model_version = db.query(ModelVersion).filter(
            ModelVersion.scene_id == scene_id,
            ModelVersion.is_default == True,
            ModelVersion.status == "active"
        ).first()
        
        if model_version:
            return model_version.model_path
        
        # 如果没有默认模型，使用预训练模型
        return "yolov11n.pt"
    
    async def detect_single(
        self,
        db: Session,
        scene_id: int,
        image_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        image_size: int = 640
    ) -> Dict[str, Any]:
        """
        单图检测
        
        Args:
            db: 数据库会话
            scene_id: 场景ID
            image_path: 图像路径
            conf_threshold: 置信度阈值
            iou_threshold: IoU 阈值
            image_size: 推理图像尺寸
        
        Returns:
            检测结果
        """
        start_time = time.time()
        
        # 确保模型已加载
        if scene_id not in self.models:
            model_path = self.get_default_model_path(db, scene_id)
            if not self.load_model(scene_id, model_path):
                raise ValueError(f"无法加载模型: scene_id={scene_id}")
        
        model = self.models[scene_id]
        
        # 执行检测
        results = model.predict(
            source=image_path,
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=image_size,
            verbose=False
        )
        
        inference_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        # 解析结果
        detections = []
        if results and len(results) > 0:
            result = results[0]
            img_height, img_width = result.orig_shape
            
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = result.names[class_id]
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                
                detections.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": bbox,
                    "image_width": img_width,
                    "image_height": img_height
                })
        
        return {
            "image_path": image_path,
            "detections": detections,
            "total_objects": len(detections),
            "inference_time": inference_time,
            "conf_threshold": conf_threshold,
            "iou_threshold": iou_threshold,
            "image_size": image_size
        }
    
    async def detect_batch(
        self,
        db: Session,
        scene_id: int,
        image_paths: List[str],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        image_size: int = 640
    ) -> List[Dict[str, Any]]:
        """
        批量检测
        
        Args:
            db: 数据库会话
            scene_id: 场景ID
            image_paths: 图像路径列表
            conf_threshold: 置信度阈值
            iou_threshold: IoU 阈值
            image_size: 推理图像尺寸
        
        Returns:
            检测结果列表
        """
        results = []
        for image_path in image_paths:
            try:
                result = await self.detect_single(
                    db=db,
                    scene_id=scene_id,
                    image_path=image_path,
                    conf_threshold=conf_threshold,
                    iou_threshold=iou_threshold,
                    image_size=image_size
                )
                results.append(result)
            except Exception as e:
                logger.error(f"检测失败 {image_path}: {e}")
                results.append({
                    "image_path": image_path,
                    "error": str(e),
                    "detections": []
                })
        
        return results
    
    async def detect_video(
        self,
        db: Session,
        scene_id: int,
        video_path: str,
        output_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        image_size: int = 640,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        视频检测
        
        Args:
            db: 数据库会话
            scene_id: 场景ID
            video_path: 视频路径
            output_path: 输出视频路径
            conf_threshold: 置信度阈值
            iou_threshold: IoU 阈值
            image_size: 推理图像尺寸
            progress_callback: 进度回调函数
        
        Returns:
            检测结果
        """
        # 确保模型已加载
        if scene_id not in self.models:
            model_path = self.get_default_model_path(db, scene_id)
            if not self.load_model(scene_id, model_path):
                raise ValueError(f"无法加载模型: scene_id={scene_id}")
        
        model = self.models[scene_id]
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        total_objects = 0
        start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 执行检测
                results = model.predict(
                    source=frame,
                    conf=conf_threshold,
                    iou=iou_threshold,
                    imgsz=image_size,
                    verbose=False
                )
                
                # 绘制检测结果
                if results and len(results) > 0:
                    annotated_frame = results[0].plot()
                    out.write(annotated_frame)
                    total_objects += len(results[0].boxes)
                else:
                    out.write(frame)
                
                frame_count += 1
                
                # 更新进度
                if progress_callback and total_frames > 0:
                    progress = int((frame_count / total_frames) * 100)
                    progress_callback(progress)
            
            inference_time = (time.time() - start_time) * 1000
            
            return {
                "video_path": video_path,
                "output_path": output_path,
                "total_frames": frame_count,
                "total_objects": total_objects,
                "inference_time": inference_time,
                "fps": fps
            }
        
        finally:
            cap.release()
            out.release()
    
    async def save_detection_result(
        self,
        db: Session,
        user_id: int,
        scene_id: int,
        task_type: str,
        detections: List[Dict[str, Any]],
        image_path: str,
        annotated_image_path: Optional[str] = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        image_size: int = 640
    ) -> DetectionTask:
        """
        保存检测结果到数据库
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            scene_id: 场景ID
            task_type: 检测类型
            detections: 检测结果列表
            image_path: 原始图像路径
            annotated_image_path: 标注图像路径
            conf_threshold: 置信度阈值
            iou_threshold: IoU 阈值
            image_size: 推理图像尺寸
        
        Returns:
            检测任务
        """
        # 创建检测任务
        task = DetectionTask(
            user_id=user_id,
            scene_id=scene_id,
            task_type=task_type,
            status="completed",
            total_images=1,
            total_objects=len(detections),
            total_inference_time=sum(d.get("inference_time", 0) for d in detections),
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            image_size=image_size,
            completed_at=datetime.now()
        )
        db.add(task)
        db.flush()
        
        # 上传标注图像到 MinIO
        annotated_image_url = None
        if annotated_image_path and os.path.exists(annotated_image_path):
            try:
                if self.minio_client is None:
                    self.minio_client = MinIOClient()
                object_name = f"detection/{task.id}/{Path(annotated_image_path).name}"
                annotated_image_url = self.minio_client.upload_file(
                    object_name,
                    annotated_image_path
                )
            except Exception as e:
                logger.error(f"上传标注图像失败: {e}")
        
        # 保存检测结果
        for det in detections:
            result = DetectionResult(
                task_id=task.id,
                image_path=image_path,
                annotated_image_url=annotated_image_url,
                class_name=det.get("class_name", ""),
                class_id=det.get("class_id", 0),
                confidence=det.get("confidence", 0),
                bbox=det.get("bbox", []),
                image_width=det.get("image_width"),
                image_height=det.get("image_height"),
                inference_time=det.get("inference_time")
            )
            db.add(result)
        
        db.commit()
        db.refresh(task)
        
        return task
    
    def get_task_list(
        self,
        db: Session,
        user_id: Optional[int] = None,
        scene_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取检测任务列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID（可选）
            scene_id: 场景ID（可选）
            page: 页码
            page_size: 每页数量
        
        Returns:
            分页结果
        """
        query = db.query(DetectionTask)
        
        if user_id:
            query = query.filter(DetectionTask.user_id == user_id)
        if scene_id:
            query = query.filter(DetectionTask.scene_id == scene_id)
        
        total = query.count()
        tasks = query.order_by(DetectionTask.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": t.id,
                    "task_type": t.task_type,
                    "status": t.status,
                    "total_images": t.total_images,
                    "total_objects": t.total_objects,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in tasks
            ]
        }
    
    def get_task_results(
        self,
        db: Session,
        task_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        获取检测任务结果
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            page: 页码
            page_size: 每页数量
        
        Returns:
            分页结果
        """
        query = db.query(DetectionResult).filter(DetectionResult.task_id == task_id)
        
        total = query.count()
        results = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": r.id,
                    "image_path": r.image_path,
                    "annotated_image_url": r.annotated_image_url,
                    "class_name": r.class_name,
                    "class_id": r.class_id,
                    "confidence": r.confidence,
                    "bbox": r.bbox,
                    "image_width": r.image_width,
                    "image_height": r.image_height,
                    "inference_time": r.inference_time
                }
                for r in results
            ]
        }


# 全局检测服务实例
detection_service = DetectionService()
