"""
猫咪管理相关 Schema — 对齐成员4 的 cats.py API
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════
# 猫咪档案
# ══════════════════════════════════════════════════════════════

class CatBrief(BaseModel):
    """猫咪简要信息（嵌入在 Encounter 响应中）"""
    id: int
    code: str
    name: str
    coat_color: str
    cover_image_url: str

    model_config = {"from_attributes": True}


class CatResponse(BaseModel):
    """猫咪档案响应"""
    id: int
    code: str
    name: str
    coat_color: str
    age_stage: str
    gender: str
    personality_tags: str
    adoption_status: str
    last_seen_at: Optional[datetime] = None
    cover_image_url: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CatDetailResponse(CatResponse):
    """猫咪详情（含观察记录和出现事件）"""
    observations: list["ObservationResponse"] = []
    encounters: list["EncounterResponse"] = []


# ══════════════════════════════════════════════════════════════
# 观察记录
# ══════════════════════════════════════════════════════════════

class ObservationResponse(BaseModel):
    """观察记录响应"""
    id: int
    cat_id: int
    encounter_id: Optional[int] = None
    observed_at: datetime
    mood_status: str
    visible_health_status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
# 出现事件
# ══════════════════════════════════════════════════════════════

class EncounterResponse(BaseModel):
    """出现事件响应"""
    id: int
    cat_id: int
    cat: Optional[CatBrief] = None
    user_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: str
    occurred_at: Optional[datetime] = None
    status: str
    result_analysis: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
# 领养
# ══════════════════════════════════════════════════════════════

class AdoptionApplicationResponse(BaseModel):
    """领养申请响应"""
    id: int
    user_id: int
    cat_id: int
    cat: Optional[CatBrief] = None
    applicant_name: str
    phone: str
    address: Optional[str] = None
    reason: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════
# 猫咪关怀（关注/推荐）
# ══════════════════════════════════════════════════════════════

class AttentionCatResponse(CatResponse):
    """关注猫咪响应（含健康状态汇总）"""
    latest_mood: Optional[str] = None
    latest_health: Optional[str] = None
    observation_count: int = 0