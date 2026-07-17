# -*- coding: utf-8 -*-
"""
猫咪档案管理 API 路由（成员4 设计）
接口：
- GET  /api/cats/                    — 猫咪列表（筛选/搜索/分页）
- GET  /api/cats/recommendations/adoption — 领养推荐
- GET  /api/cats/attention           — 关注猫咪（需观察）
- GET  /api/cats/encounters          — 最近出现事件
- GET  /api/cats/{cat_id}            — 猫咪详情
- GET  /api/cats/{cat_id}/observations — 观察记录
"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, case

from app.database.session import get_db
from app.entity.db_models import Cat, Encounter, Observation, EncounterImage
from app.entity.schemas import (
    ApiResponse,
    CatResponse,
    CatDetailResponse,
    ObservationResponse,
    EncounterResponse,
    CatBrief,
    AttentionCatResponse,
)

router = APIRouter(prefix="/api/cats", tags=["猫咪档案"])


def _cat_to_response(cat: Cat) -> CatResponse:
    return CatResponse(
        id=cat.id,
        code=cat.code,
        name=cat.name,
        coat_color=cat.coat_color,
        age_stage=cat.age_stage,
        gender=cat.gender,
        personality_tags=cat.personality_tags,
        adoption_status=cat.adoption_status,
        last_seen_at=cat.last_seen_at,
        cover_image_url=cat.cover_image_url,
        description=cat.description,
        created_at=cat.created_at,
        updated_at=cat.updated_at,
    )


def _encounter_to_response(enc: Encounter) -> EncounterResponse:
    return EncounterResponse(
        id=enc.id,
        cat_id=enc.cat_id,
        cat=CatBrief(
            id=enc.cat.id,
            code=enc.cat.code,
            name=enc.cat.name,
            coat_color=enc.cat.coat_color,
            cover_image_url=enc.cat.cover_image_url,
        ) if enc.cat else None,
        user_id=enc.user_id,
        title=enc.title,
        description=enc.description,
        location=enc.location,
        occurred_at=enc.occurred_at,
        status=enc.status,
        result_analysis=enc.result_analysis,
        created_at=enc.created_at,
        updated_at=enc.updated_at,
    )


@router.get("", response_model=ApiResponse)
async def list_cats(
    keyword: str = Query(None, description="搜索关键词（名称/编号/花色）"),
    coat_color: str = Query(None, description="花色筛选"),
    age_stage: str = Query(None, description="年龄阶段"),
    gender: str = Query(None, description="性别"),
    adoption_status: str = Query(None, description="领养状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
):
    """猫咪列表 — 支持筛选和搜索"""
    query = db.query(Cat)

    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            (Cat.name.ilike(kw)) | (Cat.code.ilike(kw)) | (Cat.coat_color.ilike(kw))
        )
    if coat_color:
        query = query.filter(Cat.coat_color == coat_color)
    if age_stage:
        query = query.filter(Cat.age_stage == age_stage)
    if gender:
        query = query.filter(Cat.gender == gender)
    if adoption_status:
        query = query.filter(Cat.adoption_status == adoption_status)

    total = query.count()
    cats = query.order_by(Cat.code.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return ApiResponse(data={
        "items": [_cat_to_response(c).model_dump() for c in cats],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/recommendations/adoption", response_model=ApiResponse)
async def get_adoption_recommendations(
    limit: int = Query(6, ge=1, le=20, description="推荐数量"),
    db: Session = Depends(get_db),
):
    """领养推荐 — 筛选待领养状态的猫咪"""
    cats = db.query(Cat).filter(
        Cat.adoption_status == "待领养"
    ).order_by(Cat.last_seen_at.desc()).limit(limit).all()

    return ApiResponse(data=[_cat_to_response(c).model_dump() for c in cats])


@router.get("/attention", response_model=ApiResponse)
async def get_attention_cats(
    limit: int = Query(6, ge=1, le=20, description="返回数量"),
    db: Session = Depends(get_db),
):
    """关注猫咪 — 需要特别关注的猫咪（近期有异常观察或长期未出现）"""
    cats = db.query(Cat).options(
        joinedload(Cat.observations)
    ).order_by(Cat.last_seen_at.asc()).limit(limit * 2).all()

    results = []
    for cat in cats:
        if len(results) >= limit:
            break
        observations = cat.observations
        latest_mood = None
        latest_health = None
        if observations:
            latest = sorted(observations, key=lambda o: o.observed_at, reverse=True)
            if latest:
                latest_mood = latest[0].mood_status
                latest_health = latest[0].visible_health_status

        attention = AttentionCatResponse(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            coat_color=cat.coat_color,
            age_stage=cat.age_stage,
            gender=cat.gender,
            personality_tags=cat.personality_tags,
            adoption_status=cat.adoption_status,
            last_seen_at=cat.last_seen_at,
            cover_image_url=cat.cover_image_url,
            description=cat.description,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
            latest_mood=latest_mood,
            latest_health=latest_health,
            observation_count=len(observations),
        )
        results.append(attention)

    return ApiResponse(data=[r.model_dump() for r in results])


@router.get("/encounters", response_model=ApiResponse)
async def get_recent_encounters(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    status: str = Query(None, description="状态筛选"),
    db: Session = Depends(get_db),
):
    """最近出现事件 — 按时间倒序"""
    query = db.query(Encounter).options(joinedload(Encounter.cat)).order_by(desc(Encounter.occurred_at))

    if status:
        query = query.filter(Encounter.status == status)

    encounters = query.limit(limit).all()
    return ApiResponse(data=[_encounter_to_response(e).model_dump() for e in encounters])


@router.get("/{cat_id}", response_model=ApiResponse)
async def get_cat_detail(
    cat_id: int,
    db: Session = Depends(get_db),
):
    """猫咪详情 — 含观察记录和出现事件"""
    cat = db.query(Cat).options(
        joinedload(Cat.observations),
        joinedload(Cat.encounters).joinedload(Encounter.images),
    ).filter(Cat.id == cat_id).first()

    if not cat:
        return ApiResponse(code=404, message="猫咪不存在")

    detail = CatDetailResponse(
        id=cat.id,
        code=cat.code,
        name=cat.name,
        coat_color=cat.coat_color,
        age_stage=cat.age_stage,
        gender=cat.gender,
        personality_tags=cat.personality_tags,
        adoption_status=cat.adoption_status,
        last_seen_at=cat.last_seen_at,
        cover_image_url=cat.cover_image_url,
        description=cat.description,
        created_at=cat.created_at,
        updated_at=cat.updated_at,
        observations=[
            ObservationResponse(
                id=obs.id,
                cat_id=obs.cat_id,
                encounter_id=obs.encounter_id,
                observed_at=obs.observed_at,
                mood_status=obs.mood_status,
                visible_health_status=obs.visible_health_status,
                notes=obs.notes,
                created_at=obs.created_at,
            )
            for obs in sorted(cat.observations, key=lambda o: o.observed_at, reverse=True)
        ],
        encounters=[
            _encounter_to_response(enc)
            for enc in sorted(cat.encounters, key=lambda e: e.occurred_at, reverse=True)
        ],
    )

    return ApiResponse(data=detail.model_dump())


@router.get("/{cat_id}/observations", response_model=ApiResponse)
async def get_cat_observations(
    cat_id: int,
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
):
    """猫咪观察记录"""
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        return ApiResponse(code=404, message="猫咪不存在")

    observations = (
        db.query(Observation)
        .filter(Observation.cat_id == cat_id)
        .order_by(desc(Observation.observed_at))
        .limit(limit)
        .all()
    )

    return ApiResponse(data=[
        ObservationResponse(
            id=obs.id,
            cat_id=obs.cat_id,
            encounter_id=obs.encounter_id,
            observed_at=obs.observed_at,
            mood_status=obs.mood_status,
            visible_health_status=obs.visible_health_status,
            notes=obs.notes,
            created_at=obs.created_at,
        ).model_dump()
        for obs in observations
    ])