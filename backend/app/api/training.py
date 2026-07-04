"""
训练模块 API 路由
提供训练任务管理、数据集上传验证等接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.entity.db_models import User, DetectionScene
from app.entity.schemas import ApiResponse
from app.services.training_service import training_service
from app.services.data_utils import validate_dataset, split_dataset, generate_data_yaml

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
