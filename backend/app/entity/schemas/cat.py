from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CatBase(BaseModel):
    code: Optional[str] = None
    name: str
    cover_image: Optional[str] = Field(None, alias="coverImage")
    gallery_images: list[str] = Field(default_factory=list, alias="galleryImages")
    coat_color: Optional[str] = Field(None, alias="coatColor")
    age_stage: Optional[str] = Field(None, alias="ageStage")
    gender: Optional[str] = None
    personality_tags: list[str] = Field(default_factory=list, alias="personalityTags")
    health_status: Optional[str] = Field(None, alias="healthStatus")
    mood_status: Optional[str] = Field(None, alias="moodStatus")
    adoption_status: str = Field(default="暂不开放", alias="adoptionStatus")
    last_seen_location: Optional[str] = Field(None, alias="lastSeenLocation")
    last_seen_at: Optional[datetime] = Field(None, alias="lastSeenAt")
    description: Optional[str] = None
    is_focus: bool = Field(default=False, alias="isFocus")

    model_config = {"populate_by_name": True}


class CatCreate(CatBase):
    pass


class CatUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    cover_image: Optional[str] = Field(None, alias="coverImage")
    gallery_images: Optional[list[str]] = Field(None, alias="galleryImages")
    coat_color: Optional[str] = Field(None, alias="coatColor")
    age_stage: Optional[str] = Field(None, alias="ageStage")
    gender: Optional[str] = None
    personality_tags: Optional[list[str]] = Field(None, alias="personalityTags")
    health_status: Optional[str] = Field(None, alias="healthStatus")
    mood_status: Optional[str] = Field(None, alias="moodStatus")
    adoption_status: Optional[str] = Field(None, alias="adoptionStatus")
    last_seen_location: Optional[str] = Field(None, alias="lastSeenLocation")
    last_seen_at: Optional[datetime] = Field(None, alias="lastSeenAt")
    description: Optional[str] = None
    is_focus: Optional[bool] = Field(None, alias="isFocus")

    model_config = {"populate_by_name": True}


class CatResponse(CatBase):
    id: str
    mark_type: Optional[str] = Field(None, alias="_markType")
    mark_remark: Optional[str] = Field(None, alias="_markRemark")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class CatObservationCreate(BaseModel):
    location: Optional[str] = None
    mood_status: Optional[str] = Field(None, alias="moodStatus")
    health_status: Optional[str] = Field(None, alias="healthStatus")
    observed_at: Optional[datetime] = Field(None, alias="observedAt")
    description: Optional[str] = None

    model_config = {"populate_by_name": True}


class CatObservationResponse(CatObservationCreate):
    id: str
    cat_id: str = Field(..., alias="catId")
    observed_at: datetime = Field(..., alias="observedAt")
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class CatAuditRecordResponse(BaseModel):
    id: str
    cat_id: str = Field(..., alias="catId")
    action: str
    remark: str = ""
    operator: str
    operated_at: datetime = Field(..., alias="operatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class BatchMarkCatsRequest(BaseModel):
    cat_ids: list[str] = Field(..., alias="catIds")
    mark_type: str = Field(..., alias="markType")
    remark: Optional[str] = None

    model_config = {"populate_by_name": True}


class BatchCatIdsRequest(BaseModel):
    cat_ids: list[str] = Field(..., alias="catIds")

    model_config = {"populate_by_name": True}


class ToggleFocusRequest(BaseModel):
    is_focus: bool = Field(..., alias="isFocus")

    model_config = {"populate_by_name": True}


class BatchToggleFocusRequest(BatchCatIdsRequest):
    is_focus: bool = Field(..., alias="isFocus")


class CatOperationResult(BaseModel):
    success: bool
    message: Optional[str] = None
    id: Optional[str] = None
