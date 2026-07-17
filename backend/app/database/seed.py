# -*- coding: utf-8 -*-
"""
数据库种子数据模块
在应用启动时自动检查并创建默认角色和超级管理员
"""
from app.core.logger import get_logger
from app.core.security import hash_password

logger = get_logger("seed")


def seed_roles_and_admin(db_session) -> None:
    """
    初始化默认角色和超级管理员账号

    - 创建默认角色：user、admin、super_admin
    - 创建默认超级管理员：superadmin / admin123
    - 创建默认普通管理员：admin / admin123
    """
    from app.entity.db_models import User, Role

    # ── 创建默认角色 ──────────────────────────────────
    default_roles = [
        {"name": "user", "display_name": "普通用户", "description": "注册用户，可上传识别图片，查看自己的记录", "is_system": True},
        {"name": "admin", "display_name": "管理员", "description": "平台管理员，处理识别任务和猫咪档案管理", "is_system": True},
        {"name": "super_admin", "display_name": "超级管理员", "description": "总管理员，管理账号和权限", "is_system": True},
    ]

    for role_data in default_roles:
        existing = db_session.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            role = Role(**role_data)
            db_session.add(role)
            logger.info(f"创建默认角色: {role_data['display_name']}")

    db_session.commit()

    # ── 创建默认管理员 ────────────────────────────────
    default_users = [
        {
            "username": "superadmin",
            "email": "superadmin@cattrace.local",
            "password": "admin123",
            "nickname": "总管理员",
            "role": "super_admin",
            "campus_role": "总管理员",
            "bio": "负责全平台账号、管理员职责和数据范围管理。",
        },
        {
            "username": "admin",
            "email": "admin@cattrace.local",
            "password": "admin123",
            "nickname": "平台管理员",
            "role": "admin",
            "campus_role": "平台管理员",
            "bio": "负责平台数据审核、识别任务和猫咪档案管理。",
        },
    ]

    for user_data in default_users:
        existing = db_session.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                nickname=user_data["nickname"],
                role=user_data["role"],
                campus_role=user_data["campus_role"],
                bio=user_data["bio"],
                is_superuser=(user_data["role"] == "super_admin"),
            )
            db_session.add(user)
            logger.info(f"创建默认用户: {user_data['username']} ({user_data['role']})")

    db_session.commit()
    logger.info("种子数据初始化完成")