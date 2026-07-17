from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.entity.db_models import Cat, CatAuditRecord, CatObservation, Role, User, UserRole


DEFAULT_CATS = [
    {
        "code": "cat-orange",
        "name": "橘子",
        "cover_image": "https://images.unsplash.com/photo-1574158622682-e40e69881006?auto=format&fit=crop&w=900&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1574158622682-e40e69881006?auto=format&fit=crop&w=900&q=80",
            "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?auto=format&fit=crop&w=900&q=80",
            "https://images.unsplash.com/photo-1513360371669-4adf3dd7dff8?auto=format&fit=crop&w=900&q=80",
        ],
        "coat_color": "橘白",
        "age_stage": "成年",
        "gender": "公",
        "personality_tags": ["亲人", "胆大", "贪吃"],
        "health_status": "健康良好",
        "mood_status": "很放松",
        "adoption_status": "待领养",
        "last_seen_location": "校门东侧长椅",
        "last_seen_at": "2026-07-15T08:40:00",
        "description": "常在午后出现在长椅附近，愿意靠近志愿者，适合有耐心的新手领养。",
        "is_focus": False,
    },
    {
        "code": "cat-milk",
        "name": "奶盖",
        "cover_image": "https://images.unsplash.com/photo-1592194996308-7b43878e84a6?auto=format&fit=crop&w=900&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1592194996308-7b43878e84a6?auto=format&fit=crop&w=900&q=80",
            "https://images.unsplash.com/photo-1543852786-1cf6624b9987?auto=format&fit=crop&w=900&q=80",
        ],
        "coat_color": "奶牛",
        "age_stage": "幼猫",
        "gender": "母",
        "personality_tags": ["亲人", "活泼"],
        "health_status": "观察中",
        "mood_status": "好奇",
        "adoption_status": "待领养",
        "last_seen_location": "三号楼花坛",
        "last_seen_at": "2026-07-15T09:10:00",
        "description": "体型较小，喜欢跟随同伴活动，近期需要继续观察食欲和精神状态。",
        "is_focus": True,
        "mark_type": "常规标记",
        "mark_remark": "食欲监控中",
    },
    {
        "code": "cat-black",
        "name": "小黑",
        "cover_image": "https://images.unsplash.com/photo-1548802673-380ab8ebc7b7?auto=format&fit=crop&w=900&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1548802673-380ab8ebc7b7?auto=format&fit=crop&w=900&q=80",
            "https://images.unsplash.com/photo-1501820488136-72669149e0d4?auto=format&fit=crop&w=900&q=80",
        ],
        "coat_color": "黑色",
        "age_stage": "成年",
        "gender": "公",
        "personality_tags": ["安静", "警惕"],
        "health_status": "健康良好",
        "mood_status": "谨慎",
        "adoption_status": "云领养中",
        "last_seen_location": "图书馆北门",
        "last_seen_at": "2026-07-14T20:15:00",
        "description": "夜间出现频率较高，保持距离但会接受固定投喂。",
        "is_focus": False,
    },
    {
        "code": "cat-sanhua",
        "name": "三花妹妹",
        "cover_image": "https://images.unsplash.com/photo-1615789591457-74a63395c990?auto=format&fit=crop&w=900&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1615789591457-74a63395c990?auto=format&fit=crop&w=900&q=80",
            "https://images.unsplash.com/photo-1495360010541-f48722b34f7d?auto=format&fit=crop&w=900&q=80",
        ],
        "coat_color": "三花",
        "age_stage": "成年",
        "gender": "母",
        "personality_tags": ["温柔", "亲人"],
        "health_status": "健康良好",
        "mood_status": "稳定",
        "adoption_status": "已领养",
        "last_seen_location": "旧食堂后门",
        "last_seen_at": "2026-07-10T18:30:00",
        "description": "已完成领养回访，适应良好，作为成功领养案例保留档案。",
        "is_focus": False,
    },
    {
        "code": "cat-tabby",
        "name": "狸花弟弟",
        "cover_image": "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?auto=format&fit=crop&w=900&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?auto=format&fit=crop&w=900&q=80",
            "https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?auto=format&fit=crop&w=900&q=80",
        ],
        "coat_color": "狸花",
        "age_stage": "成年",
        "gender": "公",
        "personality_tags": ["独立", "机警"],
        "health_status": "需复查",
        "mood_status": "紧张",
        "adoption_status": "暂不开放",
        "last_seen_location": "操场西南角",
        "last_seen_at": "2026-07-15T07:20:00",
        "description": "右眼偶有分泌物，建议志愿者继续记录并安排复查。",
        "is_focus": True,
        "mark_type": "重点观察",
        "mark_remark": "右眼分泌物需复查",
    },
    {
        "code": "cat-white",
        "name": "白白",
        "cover_image": "https://images.unsplash.com/photo-1583795128727-6ec3642408f8?auto=format&fit=crop&w=900&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1583795128727-6ec3642408f8?auto=format&fit=crop&w=900&q=80",
            "https://images.unsplash.com/photo-1606214174585-fe31582dc6ee?auto=format&fit=crop&w=900&q=80",
        ],
        "coat_color": "白色",
        "age_stage": "成年",
        "gender": "母",
        "personality_tags": ["亲人", "安静"],
        "health_status": "健康良好",
        "mood_status": "放松",
        "adoption_status": "待领养",
        "last_seen_location": "研究生公寓门口",
        "last_seen_at": "2026-07-15T11:05:00",
        "description": "性格稳定，喜欢晒太阳，已完成基础健康检查。",
        "is_focus": False,
    },
]


DEFAULT_OBSERVATIONS = [
    {
        "cat_code": "cat-orange",
        "location": "校门东侧长椅",
        "mood_status": "很放松",
        "health_status": "健康良好",
        "observed_at": "2026-07-15T08:40:00",
        "description": "主动靠近志愿者，进食正常。",
    },
    {
        "cat_code": "cat-orange",
        "location": "一号楼前花园",
        "mood_status": "开心",
        "health_status": "健康良好",
        "observed_at": "2026-07-13T18:15:00",
        "description": "与其他猫保持友好距离。",
    },
    {
        "cat_code": "cat-milk",
        "location": "三号楼花坛",
        "mood_status": "好奇",
        "health_status": "观察中",
        "observed_at": "2026-07-15T09:10:00",
        "description": "精神较好，仍需观察食量。",
    },
    {
        "cat_code": "cat-tabby",
        "location": "操场西南角",
        "mood_status": "紧张",
        "health_status": "需复查",
        "observed_at": "2026-07-15T07:20:00",
        "description": "右眼疑似不适，已标记重点关注。",
    },
]


DEFAULT_AUDIT_RECORDS = [
    ("cat-orange", "审核通过", "档案完整，照片清晰", "管理员A", "2026-07-15T08:40:00"),
    ("cat-orange", "标记待复查", "食欲不稳定需持续观察", "管理员B", "2026-07-12T08:40:00"),
    ("cat-milk", "审核通过", "健康检查已完成", "管理员A", "2026-07-15T09:10:00"),
    ("cat-black", "审核驳回", "照片不清晰需重新提交", "管理员C", "2026-07-14T20:15:00"),
    ("cat-black", "审核通过", "补充照片后审核通过", "管理员A", "2026-07-15T20:15:00"),
    ("cat-sanhua", "审核通过", "已领养，归档处理", "管理员B", "2026-07-10T18:30:00"),
    ("cat-tabby", "标记待复查", "右眼分泌物需安排复查", "管理员C", "2026-07-15T07:20:00"),
    ("cat-white", "审核通过", "基础健康检查完成", "管理员A", "2026-07-15T11:05:00"),
]


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def seed_roles_and_admin(db: Session) -> None:
    default_roles = [
        {
            "name": "user",
            "display_name": "普通用户",
            "description": "注册用户，可上传识别图片，查看自己的记录",
            "is_system": True,
        },
        {
            "name": "admin",
            "display_name": "管理员",
            "description": "平台管理员，处理识别任务和猫咪档案管理",
            "is_system": True,
        },
        {
            "name": "super_admin",
            "display_name": "超级管理员",
            "description": "总管理员，管理账号和权限",
            "is_system": True,
        },
    ]

    for role_data in default_roles:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            db.add(Role(**role_data))

    db.commit()

    default_users = [
        {
            "username": "superadmin",
            "phone": "13900000000",
            "email": "superadmin@cattrace.local",
            "password": "admin123",
            "nickname": "总管理员",
            "role": "super_admin",
            "campus_role": "总管理员",
            "bio": "负责全平台账号、管理员职责和数据范围管理。",
            "is_superuser": True,
        },
        {
            "username": "admin",
            "phone": "13800000000",
            "email": "admin@cattrace.local",
            "password": "admin123",
            "nickname": "平台管理员",
            "role": "admin",
            "campus_role": "平台管理员",
            "bio": "负责平台数据审核、识别任务和猫咪档案管理。",
            "is_superuser": False,
        },
    ]

    for user_data in default_users:
        user = db.query(User).filter(User.username == user_data["username"]).first()
        if not user:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                phone=user_data["phone"],
                hashed_password=hash_password(user_data["password"]),
                nickname=user_data["nickname"],
                role=user_data["role"],
                campus_role=user_data["campus_role"],
                bio=user_data["bio"],
                is_superuser=user_data["is_superuser"],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif not user.phone:
            user.phone = user_data["phone"]
            db.commit()
            db.refresh(user)

        role = db.query(Role).filter(Role.name == user_data["role"]).first()
        if role:
            relation = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).first()
            if not relation:
                db.add(UserRole(user_id=user.id, role_id=role.id))

    db.commit()
    seed_cat_archives(db)


def seed_cat_archives(db: Session) -> None:
    if db.query(Cat).first():
        return

    cats_by_code: dict[str, Cat] = {}
    for cat_data in DEFAULT_CATS:
        payload = dict(cat_data)
        payload["last_seen_at"] = _parse_datetime(payload.get("last_seen_at"))
        cat = Cat(**payload)
        db.add(cat)
        cats_by_code[cat.code] = cat

    db.commit()

    for cat in cats_by_code.values():
        db.refresh(cat)

    for observation_data in DEFAULT_OBSERVATIONS:
        cat = cats_by_code.get(observation_data["cat_code"])
        if not cat:
            continue
        db.add(
            CatObservation(
                cat_id=cat.id,
                location=observation_data["location"],
                mood_status=observation_data["mood_status"],
                health_status=observation_data["health_status"],
                observed_at=_parse_datetime(observation_data["observed_at"]),
                description=observation_data["description"],
            )
        )

    for cat_code, action, remark, operator, operated_at in DEFAULT_AUDIT_RECORDS:
        cat = cats_by_code.get(cat_code)
        if not cat:
            continue
        db.add(
            CatAuditRecord(
                cat_id=cat.id,
                action=action,
                remark=remark,
                operator_name=operator,
                operated_at=_parse_datetime(operated_at),
            )
        )

    db.commit()
