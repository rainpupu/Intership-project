"""
检测模块 API 路由
提供目标检测、场景管理等接口
"""
import os
import tempfile
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.entity.db_models import User, DetectionScene
from app.entity.schemas import ApiResponse
from app.services.detection_service import detection_service

router = APIRouter(prefix="/api/detection", tags=["目标检测"])


@router.post("/single", response_model=ApiResponse)
async def detect_single(
    scene_id: int = Form(..., description="场景ID"),
    image: UploadFile = File(..., description="图像文件"),
    conf_threshold: float = Form(0.25, description="置信度阈值"),
    iou_threshold: float = Form(0.45, description="IoU阈值"),
    image_size: int = Form(640, description="推理图像尺寸"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """单图检测"""
    # 验证场景
    scene = db.query(DetectionScene).filter(DetectionScene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 保存上传的图像
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 执行检测
        result = await detection_service.detect_single(
            db=db,
            scene_id=scene_id,
            image_path=tmp_path,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            image_size=image_size
        )
        
        # 保存检测结果
        task = await detection_service.save_detection_result(
            db=db,
            user_id=current_user.id,
            scene_id=scene_id,
            task_type="single",
            detections=result["detections"],
            image_path=tmp_path,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            image_size=image_size,
            inference_time=result.get("inference_time", 0)
        )
        
        return ApiResponse(
            code=200,
            message="检测完成",
            data={
                "task_id": task.id,
                "total_objects": result["total_objects"],
                "inference_time": result["inference_time"],
                "detections": result["detections"]
            }
        )
    
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/batch", response_model=ApiResponse)
async def detect_batch(
    scene_id: int = Form(..., description="场景ID"),
    images: List[UploadFile] = File(..., description="图像文件列表"),
    conf_threshold: float = Form(0.25, description="置信度阈值"),
    iou_threshold: float = Form(0.45, description="IoU阈值"),
    image_size: int = Form(640, description="推理图像尺寸"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量检测"""
    # 验证场景
    scene = db.query(DetectionScene).filter(DetectionScene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 保存上传的图像
    temp_paths = []
    for image in images:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await image.read()
            tmp.write(content)
            temp_paths.append(tmp.name)
    
    try:
        # 执行批量检测
        results = await detection_service.detect_batch(
            db=db,
            scene_id=scene_id,
            image_paths=temp_paths,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            image_size=image_size
        )
        
        # 保存检测结果
        total_objects = 0
        for result in results:
            if "error" not in result:
                await detection_service.save_detection_result(
                    db=db,
                    user_id=current_user.id,
                    scene_id=scene_id,
                    task_type="batch",
                    detections=result["detections"],
                    image_path=result["image_path"],
                    conf_threshold=conf_threshold,
                    iou_threshold=iou_threshold,
                    image_size=image_size,
                    inference_time=result.get("inference_time", 0)
                )
                total_objects += result["total_objects"]
        
        return ApiResponse(
            code=200,
            message="批量检测完成",
            data={
                "total_images": len(images),
                "total_objects": total_objects,
                "results": results
            }
        )
    
    finally:
        # 清理临时文件
        for path in temp_paths:
            if os.path.exists(path):
                os.unlink(path)


@router.post("/video", response_model=ApiResponse)
async def detect_video(
    scene_id: int = Form(..., description="场景ID"),
    video: UploadFile = File(..., description="视频文件"),
    conf_threshold: float = Form(0.25, description="置信度阈值"),
    iou_threshold: float = Form(0.45, description="IoU阈值"),
    image_size: int = Form(640, description="推理图像尺寸"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """视频检测"""
    # 验证场景
    scene = db.query(DetectionScene).filter(DetectionScene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 保存上传的视频
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        content = await video.read()
        tmp.write(content)
        video_path = tmp.name
    
    # 输出视频路径
    output_path = video_path.replace(".mp4", "_detected.mp4")
    
    try:
        # 执行视频检测
        result = await detection_service.detect_video(
            db=db,
            scene_id=scene_id,
            video_path=video_path,
            output_path=output_path,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            image_size=image_size
        )
        
        # 上传结果视频到 MinIO
        from app.storage.minio_client import minio_client
        object_name = f"detection/video/{os.path.basename(output_path)}"
        video_url = minio_client.upload_file(output_path, object_name)
        
        return ApiResponse(
            code=200,
            message="视频检测完成",
            data={
                "total_frames": result["total_frames"],
                "total_objects": result["total_objects"],
                "inference_time": result["inference_time"],
                "video_url": video_url
            }
        )
    
    finally:
        # 清理临时文件
        if os.path.exists(video_path):
            os.unlink(video_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


@router.get("/tasks/{task_id}", response_model=ApiResponse)
async def get_detection_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取检测任务详情"""
    from app.entity.db_models import DetectionTask
    
    task = db.query(DetectionTask).filter(DetectionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="检测任务不存在")
    
    return ApiResponse(
        code=200,
        data={
            "id": task.id,
            "task_type": task.task_type,
            "status": task.status,
            "total_images": task.total_images,
            "total_objects": task.total_objects,
            "total_inference_time": task.total_inference_time,
            "conf_threshold": task.conf_threshold,
            "iou_threshold": task.iou_threshold,
            "image_size": task.image_size,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
    )


@router.get("/tasks/{task_id}/results", response_model=ApiResponse)
async def get_detection_results(
    task_id: int,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取检测结果"""
    result = detection_service.get_task_results(
        db=db,
        task_id=task_id,
        page=page,
        page_size=page_size
    )
    
    return ApiResponse(code=200, data=result)


@router.get("/tasks", response_model=ApiResponse)
async def get_detection_tasks(
    scene_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取检测任务列表"""
    result = detection_service.get_task_list(
        db=db,
        user_id=current_user.id,
        scene_id=scene_id,
        page=page,
        page_size=page_size
    )
    
    return ApiResponse(code=200, data=result)


@router.get("/scenes", response_model=ApiResponse)
async def get_detection_scenes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取检测场景列表（带 Redis 缓存）"""
    from app.storage.redis_client import redis_client
    
    # 尝试从缓存获取
    cache_key = "detection_scenes:active"
    cached = redis_client.cache_get("scenes", cache_key)
    if cached is not None:
        return ApiResponse(code=200, data=cached)
    
    # 缓存未命中，查询数据库
    scenes = db.query(DetectionScene).filter(
        DetectionScene.is_active == True
    ).all()
    
    result = [
        {
            "id": s.id,
            "name": s.name,
            "display_name": s.display_name,
            "description": s.description,
            "category": s.category,
            "class_names": s.class_names,
            "class_names_cn": s.class_names_cn
        }
        for s in scenes
    ]
    
    # 写入缓存（1小时过期）
    redis_client.cache_set("scenes", cache_key, result, ex=3600)
    
    return ApiResponse(code=200, data=result)


@router.post("/scenes", response_model=ApiResponse)
async def create_detection_scene(
    name: str = Form(..., description="场景标识"),
    display_name: str = Form(..., description="场景显示名"),
    description: str = Form("", description="场景描述"),
    category: str = Form(..., description="场景分类"),
    class_names: str = Form(..., description="类别名称，逗号分隔"),
    class_names_cn: str = Form("", description="类别中文名，逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建检测场景"""
    # 检查名称是否已存在
    existing = db.query(DetectionScene).filter(DetectionScene.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="场景名称已存在")
    
    # 解析类别名称
    class_list = [n.strip() for n in class_names.split(",")]
    class_cn_list = [n.strip() for n in class_names_cn.split(",")] if class_names_cn else []
    
    # 构建中文名映射
    class_names_cn_dict = {}
    for i, cn in enumerate(class_cn_list):
        if i < len(class_list):
            class_names_cn_dict[class_list[i]] = cn
    
    scene = DetectionScene(
        name=name,
        display_name=display_name,
        description=description,
        category=category,
        class_names=class_list,
        class_names_cn=class_names_cn_dict if class_names_cn_dict else None,
        created_by=current_user.id
    )
    db.add(scene)
    db.commit()
    db.refresh(scene)
    
    return ApiResponse(
        code=200,
        message="场景创建成功",
        data={
            "id": scene.id,
            "name": scene.name,
            "display_name": scene.display_name
        }
    )
