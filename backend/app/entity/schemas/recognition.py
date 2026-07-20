from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RecognitionRecordResponse(BaseModel):
    id: str
    userId: str
    image: str
    catId: str | None = None
    catName: str
    similarity: float
    modelType: str | None = None
    breedName: str | None = None
    breedConfidence: float | None = None
    identityStatus: str | None = None
    bestIdentityMatch: dict | None = None
    healthStatus: str | None = None
    moodStatus: str | None = None
    location: str
    observedAt: str | None = None
    userRemark: str | None = None
    createdAt: str | None = None
    status: str


class RecognitionRecordListQuery(BaseModel):
    scope: str = "mine"


class ConfirmExistingCatRequest(BaseModel):
    cat_id: str


class CreateCatFromRecognitionRequest(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    last_seen_location: str | None = None


class SubmitCampusClueRequest(BaseModel):
    location: str
    observed_at: datetime | None = None
    user_remark: str | None = None
