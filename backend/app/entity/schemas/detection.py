"""
检测模块 Schema
"""

from typing import Optional
from pydantic import BaseModel


class DetectionResultItem(BaseModel):
    """单个检测结果"""

    class_id: int
    class_name: str
    confidence: float
    bbox: list[float]


class DetectionResponse(BaseModel):
    """检测响应"""

    task_id: int
    total_objects: int
    inference_time: float
    detections: list[DetectionResultItem]


class SceneResponse(BaseModel):
    """场景响应"""

    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    class_names: list[str]
    class_names_cn: Optional[dict] = None

    model_config = {"from_attributes": True}
