from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.entity.db_models import Role, User, UserRole


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
