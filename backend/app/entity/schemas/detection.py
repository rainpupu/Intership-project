"""
检测模块 Schema
"""

from typing import Optional
from pydantic import BaseModel, Field


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


# ══════════════════════════════════════════════════════════════
# 猫咪识别 — 出现事件分析
# ══════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    """出现事件分析请求（前端调用时传入 encounter_id）"""

    encounter_id: int = Field(..., description="出现事件ID")
    conf_threshold: float = Field(default=0.25, description="检测置信度阈值")


class CandidateCat(BaseModel):
    """候选猫咪数据结构"""

    cat_id: int = Field(..., description="猫咪ID")
    name: str = Field(..., description="猫咪名字")
    similarity: float = Field(..., description="相似度得分 0~1")
    ref_image_url: str = Field(..., description="参考图URL")


class AnalyzeResponse(BaseModel):
    """出现事件分析响应"""

    status: str = Field(..., description="分析状态：completed/failed")
    encounter_id: int = Field(..., description="关联的出现事件ID")
    cropped_images: list[str] = Field(default=[], description="裁剪后的猫咪图片URL列表")
    candidates: list[CandidateCat] = Field(default=[], description="Top 3 候选猫咪")
    total_images: int = Field(default=0, description="事件中的图片总数")
    detected_cats: int = Field(default=0, description="检测到的猫咪数量")
