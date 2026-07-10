"""
训练服务模块
提供 YOLOv11 模型训练的完整业务逻辑
包括创建训练任务、启动/暂停/取消训练、获取训练状态和指标
"""
import csv
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.logger import get_logger
from app.entity.db_models import TrainingTask, TrainingMetric, ModelVersion, DetectionScene

logger = get_logger("training_service")


class TrainingService:
    """训练服务类"""
    
    def __init__(self):
        self.active_tasks: Dict[int, threading.Thread] = {}
        self.task_stop_flags: Dict[int, threading.Event] = {}
        # 启动时恢复中断的任务状态
        self._recover_interrupted_tasks()
    
    def _recover_interrupted_tasks(self):
        """
        恢复因进程重启而中断的训练任务
        
        将 running 状态的任务标记为 failed，避免任务永远卡住
        """
        from app.database.session import SessionLocal
        
        db = SessionLocal()
        try:
            # 查找所有 running 状态的任务
            running_tasks = db.query(TrainingTask).filter(
                TrainingTask.status == "running"
            ).all()
            
            if running_tasks:
                logger.warning(f"发现 {len(running_tasks)} 个中断的训练任务，正在恢复状态...")
                
                for task in running_tasks:
                    task.status = "failed"
                    task.error_message = "服务重启导致训练中断"
                    task.updated_at = datetime.now()
                    logger.info(f"任务 {task.id} ({task.task_uuid}) 标记为 failed")
                
                db.commit()
                logger.info(f"已恢复 {len(running_tasks)} 个中断任务的状态")
            else:
                logger.info("没有发现中断的训练任务")
                
        except Exception as e:
            logger.error(f"恢复中断任务失败: {e}")
            db.rollback()
        finally:
            db.close()
    
    def create_training_task(
        self,
        db: Session,
        user_id: int,
        scene_id: int,
        config: Dict[str, Any]
    ) -> TrainingTask:
        """
        创建训练任务
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            scene_id: 场景ID
            config: 训练配置
        
        Returns:
            创建的训练任务
        """
        import uuid
        
        task = TrainingTask(
            user_id=user_id,
            scene_id=scene_id,
            task_uuid=str(uuid.uuid4()),
            status="pending",
            model_name=config.get("model_name", "yolov11n"),
            epochs=config.get("epochs", 100),
            img_size=config.get("img_size", 640),
            batch_size=config.get("batch_size", 16),
            device=config.get("device", "cpu"),
            optimizer=config.get("optimizer", "SGD"),
            lr0=config.get("lr0", 0.01),
            dataset_path=config.get("dataset_path"),
            data_yaml=config.get("data_yaml"),
            dataset_size=config.get("dataset_size", 0)
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"创建训练任务: task_id={task.id}, scene_id={scene_id}")
        return task
    
    def start_training(self, db: Session, task_id: int) -> bool:
        """
        启动训练任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
        
        Returns:
            是否成功启动
        """
        task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
        if not task:
            logger.error(f"训练任务不存在: task_id={task_id}")
            return False
        
        if task.status not in ["pending", "paused", "failed"]:
            logger.error(f"任务状态不允许启动: task_id={task_id}, status={task.status}")
            return False
        
        # 更新任务状态
        task.status = "running"
        task.started_at = datetime.now()
        task.error_message = None
        db.commit()
        
        # 创建停止标志
        stop_flag = threading.Event()
        self.task_stop_flags[task_id] = stop_flag
        
        # 启动后台训练线程
        thread = threading.Thread(
            target=self._train_worker,
            args=(task_id, stop_flag),
            daemon=True
        )
        self.active_tasks[task_id] = thread
        thread.start()
        
        logger.info(f"启动训练任务: task_id={task_id}")
        return True
    
    def _train_worker(self, task_id: int, stop_flag: threading.Event):
        """
        训练工作线程
        
        Args:
            task_id: 任务ID
            stop_flag: 停止标志
        """
        from app.database.session import SessionLocal
        
        db = SessionLocal()
        task = None
        try:
            task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
            if not task:
                return
            
            # 动态导入 ultralytics（避免启动时加载）
            try:
                from ultralytics import YOLO
            except ImportError:
                logger.error("ultralytics 未安装")
                task.status = "failed"
                task.error_message = "ultralytics 未安装"
                db.commit()
                return
            
            # 加载模型
            model_name = task.model_name
            model_path = f"{model_name}.pt"
            
            logger.info(f"加载模型: {model_path}")
            model = YOLO(model_path)
            
            # 准备训练参数
            train_args = {
                "data": task.data_yaml,
                "epochs": task.epochs,
                "imgsz": task.img_size,
                "batch": task.batch_size,
                "device": task.device,
                "optimizer": task.optimizer,
                "lr0": task.lr0,
                "project": os.path.join("runs", "train"),
                "name": f"task_{task_id}",
                "exist_ok": True,
                "verbose": True
            }
            
            logger.info(f"开始训练: task_id={task_id}, args={train_args}")
            
            # 执行训练
            results = model.train(**train_args)
            
            # 检查是否被取消
            if stop_flag.is_set():
                task.status = "cancelled"
                logger.info(f"训练任务已取消: task_id={task_id}")
            else:
                # 训练完成
                task.status = "completed"
                task.completed_at = datetime.now()
                task.progress = 100
                task.current_epoch = task.epochs
                
                # 保存模型版本
                best_model_path = os.path.join("runs", "train", f"task_{task_id}", "weights", "best.pt")
                if os.path.exists(best_model_path):
                    self._save_model_version(db, task, best_model_path)
                
                logger.info(f"训练任务完成: task_id={task_id}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"训练任务失败: task_id={task_id}, error={e}")
            if task is not None:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
        finally:
            # 清理
            self.active_tasks.pop(task_id, None)
            self.task_stop_flags.pop(task_id, None)
            db.close()
    
    def _save_model_version(self, db: Session, task: TrainingTask, model_path: str):
        """
        保存模型版本
        
        Args:
            db: 数据库会话
            task: 训练任务
            model_path: 模型文件路径
        """
        # 获取当前场景的版本数量
        version_count = db.query(ModelVersion).filter(
            ModelVersion.scene_id == task.scene_id
        ).count()
        
        version = ModelVersion(
            scene_id=task.scene_id,
            training_task_id=task.id,
            version=f"v{version_count + 1}.0.0",
            model_name=f"{task.model_name}_task_{task.id}",
            model_type=task.model_name,
            status="active",
            model_path=model_path,
            is_default=(version_count == 0)  # 第一个模型设为默认
        )
        
        db.add(version)
        db.commit()
        logger.info(f"保存模型版本: version={version.version}, path={model_path}")
    
    def pause_training(self, db: Session, task_id: int) -> bool:
        """
        暂停训练任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
        
        Returns:
            是否成功暂停
        """
        task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
        if not task:
            return False
        
        if task.status != "running":
            return False
        
        # 设置停止标志
        stop_flag = self.task_stop_flags.get(task_id)
        if stop_flag:
            stop_flag.set()
        
        task.status = "paused"
        db.commit()
        
        logger.info(f"暂停训练任务: task_id={task_id}")
        return True
    
    def cancel_training(self, db: Session, task_id: int) -> bool:
        """
        取消训练任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
        
        Returns:
            是否成功取消
        """
        task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
        if not task:
            return False
        
        if task.status not in ["running", "paused", "pending"]:
            return False
        
        # 设置停止标志
        stop_flag = self.task_stop_flags.get(task_id)
        if stop_flag:
            stop_flag.set()
        
        task.status = "cancelled"
        db.commit()
        
        logger.info(f"取消训练任务: task_id={task_id}")
        return True
    
    def get_training_status(self, db: Session, task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取训练状态
        
        Args:
            db: 数据库会话
            task_id: 任务ID
        
        Returns:
            训练状态字典
        """
        task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
        if not task:
            return None
        
        return {
            "task_id": task.id,
            "status": task.status,
            "current_epoch": task.current_epoch,
            "total_epochs": task.epochs,
            "progress": task.progress,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message
        }
    
    def get_training_metrics(self, db: Session, task_id: int) -> List[Dict[str, Any]]:
        """
        获取训练指标
        
        Args:
            db: 数据库会话
            task_id: 任务ID
        
        Returns:
            训练指标列表
        """
        metrics = db.query(TrainingMetric).filter(
            TrainingMetric.task_id == task_id
        ).order_by(TrainingMetric.epoch).all()
        
        return [
            {
                "epoch": m.epoch,
                "box_loss": m.box_loss,
                "cls_loss": m.cls_loss,
                "dfl_loss": m.dfl_loss,
                "precision": m.precision,
                "recall": m.recall,
                "map50": m.map50,
                "map50_95": m.map50_95,
                "lr": m.lr
            }
            for m in metrics
        ]
    
    def parse_results_csv(self, db: Session, task_id: int, results_csv: str) -> bool:
        """
        解析训练日志 results.csv
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            results_csv: results.csv 文件路径
        
        Returns:
            是否成功解析
        """
        try:
            if not os.path.exists(results_csv):
                logger.warning(f"results.csv 不存在: {results_csv}")
                return False
            
            with open(results_csv, "r") as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    epoch = int(row.get("epoch", 0))
                    
                    # 检查是否已存在
                    existing = db.query(TrainingMetric).filter(
                        TrainingMetric.task_id == task_id,
                        TrainingMetric.epoch == epoch
                    ).first()
                    
                    if existing:
                        continue
                    
                    # 创建指标记录
                    metric = TrainingMetric(
                        task_id=task_id,
                        epoch=epoch,
                        box_loss=float(row.get("train/box_loss", 0)),
                        cls_loss=float(row.get("train/cls_loss", 0)),
                        dfl_loss=float(row.get("train/dfl_loss", 0)),
                        precision=float(row.get("metrics/precision(B)", 0)),
                        recall=float(row.get("metrics/recall(B)", 0)),
                        map50=float(row.get("metrics/mAP50(B)", 0)),
                        map50_95=float(row.get("metrics/mAP50-95(B)", 0)),
                        lr=float(row.get("lr/pg0", 0))
                    )
                    db.add(metric)
                
                db.commit()
                logger.info(f"解析 results.csv 完成: task_id={task_id}")
                return True
                
        except Exception as e:
            logger.error(f"解析 results.csv 失败: {e}")
            return False
    
    def validate_model(
        self,
        db: Session,
        task_id: int,
        data_yaml: Optional[str] = None,
        img_size: int = 640,
        batch_size: int = 16
    ) -> Optional[Dict[str, Any]]:
        """
        模型评估
        
        Args:
            db: 数据库会话
            task_id: 训练任务ID
            data_yaml: 数据集配置文件路径（可选，默认使用训练时的配置）
            img_size: 图像尺寸
            batch_size: 批次大小
        
        Returns:
            评估结果字典
        """
        import threading
        
        # 获取任务信息
        task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
        if not task:
            logger.error(f"训练任务不存在: task_id={task_id}")
            return None
        
        # 检查任务状态
        if task.status not in ["completed", "failed"]:
            logger.error(f"任务状态不允许评估: task_id={task_id}, status={task.status}")
            return None
        
        # 获取模型路径
        model_version = db.query(ModelVersion).filter(
            ModelVersion.training_task_id == task_id,
            ModelVersion.status == "active"
        ).first()
        
        if not model_version:
            logger.error(f"未找到训练产出的模型: task_id={task_id}")
            return None
        
        model_path = model_version.model_path
        if not os.path.exists(model_path):
            logger.error(f"模型文件不存在: {model_path}")
            return None
        
        # 使用训练时的数据集配置或指定的配置
        eval_data_yaml = data_yaml or task.data_yaml
        if not eval_data_yaml:
            logger.error(f"未指定数据集配置: task_id={task_id}")
            return None
        
        try:
            from ultralytics import YOLO
            
            logger.info(f"开始模型评估: task_id={task_id}, model={model_path}")
            
            # 加载模型
            model = YOLO(model_path)
            
            # 执行评估
            results = model.val(
                data=eval_data_yaml,
                imgsz=img_size,
                batch=batch_size,
                verbose=True
            )
            
            # 提取评估指标
            eval_result = {
                "task_id": task_id,
                "model_path": model_path,
                "metrics": {
                    "mAP50": float(results.box.map50),
                    "mAP50-95": float(results.box.map),
                    "precision": float(results.box.mp),
                    "recall": float(results.box.mr),
                    "f1": float(results.box.f1),
                },
                "per_class_ap": {},
                "confusion_matrix": results.confusion_matrix.matrix.tolist() if results.confusion_matrix else None,
                "evaluated_at": datetime.now().isoformat()
            }
            
            # 提取各类别 AP
            if hasattr(results.box, 'ap_class_index') and hasattr(results, 'names'):
                for idx, ap in enumerate(results.box.ap):
                    class_name = results.names.get(idx, f"class_{idx}")
                    eval_result["per_class_ap"][class_name] = float(ap)
            
            # 更新模型版本的评估指标
            model_version.map50 = eval_result["metrics"]["mAP50"]
            model_version.map50_95 = eval_result["metrics"]["mAP50-95"]
            model_version.precision = eval_result["metrics"]["precision"]
            model_version.recall = eval_result["metrics"]["recall"]
            model_version.per_class_ap = eval_result["per_class_ap"]
            db.commit()
            
            logger.info(f"模型评估完成: task_id={task_id}, mAP50={eval_result['metrics']['mAP50']:.4f}")
            return eval_result
            
        except Exception as e:
            logger.error(f"模型评估失败: task_id={task_id}, error={e}")
            return None
    
    def get_task_list(
        self,
        db: Session,
        user_id: Optional[int] = None,
        scene_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取训练任务列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID（可选）
            scene_id: 场景ID（可选）
            status: 状态（可选）
            page: 页码
            page_size: 每页数量
        
        Returns:
            分页结果
        """
        query = db.query(TrainingTask)
        
        if user_id:
            query = query.filter(TrainingTask.user_id == user_id)
        if scene_id:
            query = query.filter(TrainingTask.scene_id == scene_id)
        if status:
            query = query.filter(TrainingTask.status == status)
        
        total = query.count()
        tasks = query.order_by(TrainingTask.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": t.id,
                    "task_uuid": t.task_uuid,
                    "status": t.status,
                    "scene_id": t.scene_id,
                    "model_name": t.model_name,
                    "epochs": t.epochs,
                    "current_epoch": t.current_epoch,
                    "progress": t.progress,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in tasks
            ]
        }


    # ══════════════════════════════════════════════════════════════
    # 模型版本管理
    # ══════════════════════════════════════════════════════════════

    def get_model_by_id(self, db: Session, model_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个模型版本详情

        Args:
            db: 数据库会话
            model_id: 模型版本ID

        Returns:
            模型版本信息字典
        """
        model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        if not model:
            return None

        scene = db.query(DetectionScene).filter(DetectionScene.id == model.scene_id).first()

        return {
            "id": model.id,
            "scene_id": model.scene_id,
            "scene_name": scene.name if scene else None,
            "scene_display_name": scene.display_name if scene else None,
            "training_task_id": model.training_task_id,
            "version": model.version,
            "model_name": model.model_name,
            "model_type": model.model_type,
            "status": model.status,
            "model_path": model.model_path,
            "minio_url": model.minio_url,
            "map50": model.map50,
            "map50_95": model.map50_95,
            "precision": model.precision,
            "recall": model.recall,
            "per_class_ap": model.per_class_ap,
            "description": model.description,
            "file_size": model.file_size,
            "is_default": model.is_default,
            "created_at": model.created_at.isoformat() if model.created_at else None,
        }

    def get_model_list(
        self,
        db: Session,
        scene_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取模型版本列表（分页）

        Args:
            db: 数据库会话
            scene_id: 场景ID（可选）
            status: 状态过滤（可选）
            page: 页码
            page_size: 每页数量

        Returns:
            分页结果
        """
        query = db.query(ModelVersion)

        if scene_id is not None:
            query = query.filter(ModelVersion.scene_id == scene_id)
        if status:
            query = query.filter(ModelVersion.status == status)

        total = query.count()
        models = query.order_by(ModelVersion.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": m.id,
                    "scene_id": m.scene_id,
                    "training_task_id": m.training_task_id,
                    "version": m.version,
                    "model_name": m.model_name,
                    "model_type": m.model_type,
                    "status": m.status,
                    "map50": m.map50,
                    "map50_95": m.map50_95,
                    "precision": m.precision,
                    "recall": m.recall,
                    "description": m.description,
                    "file_size": m.file_size,
                    "is_default": m.is_default,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in models
            ]
        }

    def update_model(
        self,
        db: Session,
        model_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        更新模型版本信息

        Args:
            db: 数据库会话
            model_id: 模型版本ID
            updates: 更新字段字典（允许：version, description, status, is_default, model_name）

        Returns:
            更新后的模型版本信息
        """
        model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        if not model:
            return None

        allowed_fields = {"version", "description", "status", "is_default", "model_name"}
        for key, value in updates.items():
            if key in allowed_fields and value is not None:
                # 如果更新 is_default，需要处理唯一性
                if key == "is_default" and value:
                    db.query(ModelVersion).filter(
                        ModelVersion.scene_id == model.scene_id,
                        ModelVersion.is_default == True,
                        ModelVersion.id != model_id
                    ).update({"is_default": False})
                setattr(model, key, value)

        db.commit()
        db.refresh(model)

        return self.get_model_by_id(db, model_id)

    def delete_model(self, db: Session, model_id: int, hard_delete: bool = False) -> bool:
        """
        删除模型版本

        Args:
            db: 数据库会话
            model_id: 模型版本ID
            hard_delete: True=硬删除（删记录+删文件），False=软删除（status=deleted）

        Returns:
            是否成功
        """
        model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        if not model:
            return False

        if hard_delete:
            # 删除模型文件
            if model.model_path and os.path.exists(model.model_path):
                try:
                    os.remove(model.model_path)
                    logger.info(f"删除模型文件: {model.model_path}")
                except Exception as e:
                    logger.error(f"删除模型文件失败 {model.model_path}: {e}")

            db.delete(model)
        else:
            model.status = "deleted"
            # 如果是默认模型，取消默认
            if model.is_default:
                model.is_default = False

        db.commit()
        logger.info(f"删除模型版本: model_id={model_id}, hard_delete={hard_delete}")
        return True

    def set_default_model(self, db: Session, model_id: int) -> Optional[Dict[str, Any]]:
        """
        设置模型为场景默认模型

        Args:
            db: 数据库会话
            model_id: 模型版本ID

        Returns:
            更新后的模型版本信息
        """
        model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        if not model:
            return None

        if model.status != "active":
            logger.warning(f"模型状态不是 active，无法设为默认: model_id={model_id}, status={model.status}")
            return None

        # 取消该场景其他模型的默认标志
        db.query(ModelVersion).filter(
            ModelVersion.scene_id == model.scene_id,
            ModelVersion.is_default == True,
            ModelVersion.id != model_id
        ).update({"is_default": False})

        # 设置当前模型为默认
        model.is_default = True
        db.commit()
        db.refresh(model)

        logger.info(f"设置默认模型: model_id={model_id}, scene_id={model.scene_id}")
        return self.get_model_by_id(db, model_id)


# 全局训练服务实例
training_service = TrainingService()
