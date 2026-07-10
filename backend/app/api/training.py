"""
训练模块 API 路由
提供训练任务管理、数据集上传验证等接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.logger import get_logger
from app.database.session import get_db
from app.entity.db_models import User, DetectionScene
from app.entity.schemas import ApiResponse
from app.services.training_service import training_service
from app.services.data_utils import validate_dataset, split_dataset, generate_data_yaml, convert_voc_to_yolo, convert_coco_to_yolo, convert_labelme_to_yolo

logger = get_logger("training_api")

router = APIRouter(prefix="/api/training", tags=["训练管理"])


@router.post("/tasks", response_model=ApiResponse)
async def create_training_task(
    scene_id: int = Form(..., description="场景ID"),
    model_name: str = Form("yolov11n", description="基础模型：yolov11n/s/m/l/x"),
    epochs: int = Form(100, description="训练轮数"),
    img_size: int = Form(640, description="图像尺寸"),
    batch_size: int = Form(16, description="批次大小"),
    device: str = Form("cpu", description="训练设备：0/1/cpu"),
    optimizer: str = Form("SGD", description="优化器：SGD/Adam/AdamW"),
    lr0: float = Form(0.01, description="初始学习率"),
    dataset_path: str = Form(..., description="数据集路径"),
    data_yaml: str = Form(..., description="data.yaml 路径"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建训练任务"""
    # 验证场景是否存在
    scene = db.query(DetectionScene).filter(DetectionScene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    config = {
        "model_name": model_name,
        "epochs": epochs,
        "img_size": img_size,
        "batch_size": batch_size,
        "device": device,
        "optimizer": optimizer,
        "lr0": lr0,
        "dataset_path": dataset_path,
        "data_yaml": data_yaml
    }
    
    task = training_service.create_training_task(
        db=db,
        user_id=current_user.id,
        scene_id=scene_id,
        config=config
    )
    
    return ApiResponse(
        code=200,
        message="训练任务创建成功",
        data={
            "task_id": task.id,
            "task_uuid": task.task_uuid,
            "status": task.status
        }
    )


@router.post("/tasks/{task_id}/start", response_model=ApiResponse)
async def start_training(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动训练任务"""
    success = training_service.start_training(db, task_id)
    if not success:
        raise HTTPException(status_code=400, detail="启动训练失败")
    
    return ApiResponse(code=200, message="训练任务已启动")


@router.post("/tasks/{task_id}/pause", response_model=ApiResponse)
async def pause_training(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """暂停训练任务"""
    success = training_service.pause_training(db, task_id)
    if not success:
        raise HTTPException(status_code=400, detail="暂停训练失败")
    
    return ApiResponse(code=200, message="训练任务已暂停")


@router.post("/tasks/{task_id}/cancel", response_model=ApiResponse)
async def cancel_training(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消训练任务"""
    success = training_service.cancel_training(db, task_id)
    if not success:
        raise HTTPException(status_code=400, detail="取消训练失败")
    
    return ApiResponse(code=200, message="训练任务已取消")


@router.get("/tasks/{task_id}", response_model=ApiResponse)
async def get_training_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取训练任务详情"""
    status = training_service.get_training_status(db, task_id)
    if not status:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    return ApiResponse(code=200, data=status)


@router.get("/tasks/{task_id}/status", response_model=ApiResponse)
async def get_training_status(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取训练状态"""
    status = training_service.get_training_status(db, task_id)
    if not status:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    return ApiResponse(code=200, data=status)


@router.get("/tasks/{task_id}/metrics", response_model=ApiResponse)
async def get_training_metrics(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取训练指标"""
    metrics = training_service.get_training_metrics(db, task_id)
    return ApiResponse(code=200, data=metrics)


@router.post("/tasks/{task_id}/validate", response_model=ApiResponse)
async def validate_model(
    task_id: int,
    data_yaml: Optional[str] = Form(None, description="数据集配置文件路径（可选）"),
    img_size: int = Form(640, description="图像尺寸"),
    batch_size: int = Form(16, description="批次大小"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """模型评估
    
    对训练完成的模型在验证集上进行评估，返回 mAP、precision、recall 等指标
    """
    result = training_service.validate_model(
        db=db,
        task_id=task_id,
        data_yaml=data_yaml,
        img_size=img_size,
        batch_size=batch_size
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="模型评估失败，请检查任务状态和模型文件")
    
    return ApiResponse(
        code=200,
        message="模型评估完成",
        data=result
    )


@router.get("/tasks", response_model=ApiResponse)
async def get_training_tasks(
    scene_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取训练任务列表"""
    result = training_service.get_task_list(
        db=db,
        user_id=current_user.id,
        scene_id=scene_id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return ApiResponse(code=200, data=result)


@router.post("/datasets/validate", response_model=ApiResponse)
async def validate_dataset_api(
    images_dir: str = Form(..., description="图像目录路径"),
    labels_dir: str = Form(..., description="标注目录路径"),
    class_names: str = Form(..., description="类别名称，逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """验证数据集"""
    class_list = [name.strip() for name in class_names.split(",")]
    result = validate_dataset(images_dir, labels_dir, class_list)
    
    return ApiResponse(
        code=200,
        message="数据集验证完成",
        data=result
    )


@router.post("/datasets/split", response_model=ApiResponse)
async def split_dataset_api(
    images_dir: str = Form(..., description="图像目录路径"),
    labels_dir: str = Form(..., description="标注目录路径"),
    output_dir: str = Form(..., description="输出目录路径"),
    train_ratio: float = Form(0.8, description="训练集比例"),
    val_ratio: float = Form(0.1, description="验证集比例"),
    test_ratio: float = Form(0.1, description="测试集比例"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """划分数据集"""
    try:
        stats = split_dataset(
            images_dir=images_dir,
            labels_dir=labels_dir,
            output_dir=output_dir,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio
        )
        
        return ApiResponse(
            code=200,
            message="数据集划分完成",
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/datasets/generate-yaml", response_model=ApiResponse)
async def generate_data_yaml_api(
    output_path: str = Form(..., description="输出文件路径"),
    class_names: str = Form(..., description="类别名称，逗号分隔"),
    dataset_dir: str = Form(..., description="数据集根目录"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成 data.yaml 配置文件"""
    class_list = [name.strip() for name in class_names.split(",")]
    
    try:
        generate_data_yaml(
            output_path=output_path,
            class_names=class_list,
            dataset_dir=dataset_dir
        )
        
        return ApiResponse(
            code=200,
            message="data.yaml 生成成功",
            data={"path": output_path}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/upload", response_model=ApiResponse)
async def upload_model(
    scene_id: int = Form(..., description="场景ID"),
    model_file: UploadFile = File(..., description="模型文件(.pt)"),
    version: str = Form("", description="版本号，如 v1.0.0（留空则 auto_version 决定）"),
    model_name: str = Form(..., description="模型名称"),
    model_type: str = Form("yolov11n", description="模型类型：yolov11n/s/m/l/x"),
    description: str = Form("", description="模型描述"),
    is_default: bool = Form(True, description="是否设为默认模型"),
    auto_version: bool = Form(True, description="是否自动生成版本号（v1.0.0 → v1.0.1 → ...）"),
    from_training_task_id: Optional[int] = Form(None, description="关联训练任务ID（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动上传训练好的模型文件（适用于 AutoDL 等外部平台训练后导入）"""
    import os
    import shutil
    from pathlib import Path
    from datetime import datetime
    from app.entity.db_models import ModelVersion

    # 验证场景
    scene = db.query(DetectionScene).filter(DetectionScene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 验证文件类型
    if not model_file.filename.endswith('.pt'):
        raise HTTPException(status_code=400, detail="仅支持 .pt 模型文件")

    # 自动生成版本号
    if auto_version or not version:
        existing_count = db.query(ModelVersion).filter(
            ModelVersion.scene_id == scene_id
        ).count()
        version = f"v{existing_count + 1}.0.0"

    # 创建模型存储目录
    models_dir = Path("data/models") / scene.name
    models_dir.mkdir(parents=True, exist_ok=True)

    # 保存模型文件
    model_filename = f"{model_name}_{version}.pt"
    model_path = models_dir / model_filename

    with open(model_path, "wb") as buffer:
        shutil.copyfileobj(model_file.file, buffer)

    file_size = model_path.stat().st_size

    # 如果设为默认模型，先取消该场景其他默认模型
    if is_default:
        db.query(ModelVersion).filter(
            ModelVersion.scene_id == scene_id,
            ModelVersion.is_default == True
        ).update({"is_default": False})

    # 创建模型版本记录
    model_version = ModelVersion(
        scene_id=scene_id,
        training_task_id=from_training_task_id,
        version=version,
        model_name=model_name,
        model_type=model_type,
        status="active",
        model_path=str(model_path.absolute()),
        description=description or f"手动上传于 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        file_size=file_size,
        is_default=is_default
    )
    db.add(model_version)
    db.commit()
    db.refresh(model_version)

    return ApiResponse(
        code=200,
        message="模型上传成功",
        data={
            "id": model_version.id,
            "scene_id": model_version.scene_id,
            "scene_name": scene.display_name,
            "version": model_version.version,
            "model_name": model_version.model_name,
            "model_type": model_version.model_type,
            "model_path": model_version.model_path,
            "file_size": file_size,
            "is_default": model_version.is_default,
            "status": model_version.status,
            "description": model_version.description,
            "from_training_task_id": model_version.training_task_id,
            "created_at": model_version.created_at.isoformat() if model_version.created_at else None,
        }
    )


# ── 模型管理 ──────────────────────────────────────────


@router.get("/models", response_model=ApiResponse)
async def get_model_list(
    scene_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模型版本列表（分页）"""
    result = training_service.get_model_list(
        db=db,
        scene_id=scene_id,
        status=status,
        page=page,
        page_size=page_size
    )

    return ApiResponse(code=200, data=result)


@router.get("/models/{model_id}", response_model=ApiResponse)
async def get_model_detail(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模型版本详情"""
    model = training_service.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    return ApiResponse(code=200, data=model)


@router.put("/models/{model_id}", response_model=ApiResponse)
async def update_model(
    model_id: int,
    version: Optional[str] = Form(None, description="版本号"),
    model_name: Optional[str] = Form(None, description="模型名称"),
    description: Optional[str] = Form(None, description="模型描述"),
    status: Optional[str] = Form(None, description="状态：active/archived/deleted"),
    is_default: Optional[bool] = Form(None, description="是否设为默认"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模型版本信息"""
    updates = {}
    if version is not None:
        updates["version"] = version
    if model_name is not None:
        updates["model_name"] = model_name
    if description is not None:
        updates["description"] = description
    if status is not None:
        updates["status"] = status
    if is_default is not None:
        updates["is_default"] = is_default

    if not updates:
        raise HTTPException(status_code=400, detail="没有要更新的字段")

    model = training_service.update_model(db, model_id, updates)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    return ApiResponse(code=200, message="模型更新成功", data=model)


@router.delete("/models/{model_id}", response_model=ApiResponse)
async def delete_model(
    model_id: int,
    hard_delete: bool = Form(False, description="True=硬删除，False=软删除"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模型版本（默认软删除）"""
    success = training_service.delete_model(db, model_id, hard_delete=hard_delete)
    if not success:
        raise HTTPException(status_code=404, detail="模型不存在")

    return ApiResponse(code=200, message="模型删除成功")


@router.put("/models/{model_id}/set-default", response_model=ApiResponse)
async def set_default_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设置模型为场景默认模型"""
    model = training_service.set_default_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在或状态不可用")

    return ApiResponse(code=200, message="默认模型设置成功", data=model)


# ── 数据集格式转换 ──────────────────────────────────

@router.post("/datasets/convert/voc-to-yolo", response_model=ApiResponse)
async def convert_voc_to_yolo_api(
    voc_file: UploadFile = File(..., description="VOC XML 文件"),
    class_names: str = Form(..., description="类别名称，逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """VOC XML → YOLO TXT 格式转换"""
    import tempfile
    import os

    class_list = [name.strip() for name in class_names.split(",")]

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        tmp.write(await voc_file.read())
        voc_path = tmp.name

    try:
        output_dir = tempfile.mkdtemp(prefix="voc2yolo_")
        result_path = convert_voc_to_yolo(voc_path, output_dir, class_list)
        os.unlink(voc_path)

        if result_path is None:
            raise HTTPException(status_code=400, detail="VOC 转换失败")

        return ApiResponse(
            code=200,
            message="VOC → YOLO 转换成功",
            data={"output_path": result_path}
        )
    except Exception as e:
        if os.path.exists(voc_path):
            os.unlink(voc_path)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/datasets/convert/coco-to-yolo", response_model=ApiResponse)
async def convert_coco_to_yolo_api(
    coco_file: UploadFile = File(..., description="COCO JSON 文件"),
    image_dir: str = Form(..., description="图像目录路径（用于获取图像尺寸）"),
    output_dir: str = Form(..., description="YOLO 标注输出目录"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """COCO JSON → YOLO TXT 格式转换"""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp.write(await coco_file.read())
        coco_path = tmp.name

    try:
        result = convert_coco_to_yolo(coco_path, output_dir, image_dir)
        os.unlink(coco_path)

        return ApiResponse(
            code=200,
            message=f"COCO → YOLO 转换成功，共 {len(result)} 个文件",
            data={"count": len(result), "files": result}
        )
    except Exception as e:
        if os.path.exists(coco_path):
            os.unlink(coco_path)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/datasets/convert/labelme-to-yolo", response_model=ApiResponse)
async def convert_labelme_to_yolo_api(
    labelme_file: UploadFile = File(..., description="LabelMe JSON 文件"),
    class_names: str = Form(..., description="类别名称，逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """LabelMe JSON → YOLO TXT 格式转换"""
    import tempfile
    import os

    class_list = [name.strip() for name in class_names.split(",")]

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp.write(await labelme_file.read())
        labelme_path = tmp.name

    try:
        output_dir = tempfile.mkdtemp(prefix="labelme2yolo_")
        result_path = convert_labelme_to_yolo(labelme_path, output_dir, class_list)
        os.unlink(labelme_path)

        if result_path is None:
            raise HTTPException(status_code=400, detail="LabelMe 转换失败")

        return ApiResponse(
            code=200,
            message="LabelMe → YOLO 转换成功",
            data={"output_path": result_path}
        )
    except Exception as e:
        if os.path.exists(labelme_path):
            os.unlink(labelme_path)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models/{model_id}/download")
async def download_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载模型文件
    
    返回模型文件流，支持 .pt 文件下载
    """
    from fastapi.responses import FileResponse
    from app.entity.db_models import ModelVersion
    
    # 查询模型版本
    model_version = db.query(ModelVersion).filter(
        ModelVersion.id == model_id,
        ModelVersion.status == "active"
    ).first()
    
    if not model_version:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 检查模型文件是否存在
    model_path = model_version.model_path
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="模型文件不存在")
    
    # 生成下载文件名
    filename = f"{model_version.model_name}_{model_version.version}.pt"
    
    logger.info(f"用户 {current_user.username} 下载模型: {filename}")
    
    return FileResponse(
        path=model_path,
        filename=filename,
        media_type="application/octet-stream"
    )
