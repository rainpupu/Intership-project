from __future__ import annotations

from pydantic import BaseModel


class RecognitionRecordResponse(BaseModel):
    id: str
    userId: str
    image: str
    catId: str | None = None
    catName: str
    similarity: float
    healthStatus: str | None = None
    moodStatus: str | None = None
    location: str
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
