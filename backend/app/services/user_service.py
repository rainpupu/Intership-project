"""
用户服务层
处理用户注册、登录、资料更新、角色管理等业务逻辑
"""
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.security import create_access_token, hash_password, verify_password
from app.entity.db_models import User, UserRole, Role


def _user_to_profile(user: User) -> dict:
    """将 User 模型转为前端 UserProfile 格式"""
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "role": user.role,
        "email": user.email,
        "phone": user.phone,
        "campus_role": user.campus_role,
        "bio": user.bio,
    }


class UserService:
    """用户服务"""

    @staticmethod
    def register(db: Session, username: str, password: str, nickname: str) -> User:
        """用户注册，默认角色为 user"""
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")

        new_user = User(
            username=username,
            email=f"{username}@cattrace.local",
            hashed_password=hash_password(password),
            nickname=nickname,
            role="user",
            campus_role="校园志愿者",
            bio="关注校园流浪猫，希望帮助它们建立稳定档案。",
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def login(db: Session, username: str, password: str) -> User:
        """用户登录，支持用户名或邮箱"""
        user = db.query(User).filter(
            or_(User.username == username, User.email == username)
        ).first()
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        user.last_login_at = datetime.now()
        db.commit()
        return user

    @staticmethod
    def create_access_token_for_user(user: User) -> str:
        return create_access_token(data={"sub": str(user.id)})

    @staticmethod
    def get_user_roles(db: Session, user: User) -> list[str]:
        roles = (
            db.query(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user.id)
            .all()
        )
        return [role[0] for role in roles]

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_profile(db: Session, user: User) -> dict:
        """获取用户信息（前端 UserProfile 格式）"""
        return _user_to_profile(user)

    @staticmethod
    def update_profile(db: Session, user: User, payload: dict) -> User:
        """更新用户资料"""
        # 将 user 合并到当前 session（get_current_user 使用的是不同 session）
        user = db.merge(user)
        updatable_fields = ["nickname", "avatar", "email", "phone", "campus_role", "bio"]
        for field in updatable_fields:
            if field in payload and payload[field] is not None:
                setattr(user, field, payload[field])
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
        """修改密码"""
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="旧密码错误")
        user.hashed_password = hash_password(new_password)
        db.commit()

    # ══════════════════════════════════════════════════════════════
    # 超级管理员功能
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def get_user_list(
        db: Session,
        role: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> list[dict]:
        """获取用户列表（超级管理员）"""
        query = db.query(User)

        if role and role != "all":
            query = query.filter(User.role == role)

        if keyword:
            keyword = f"%{keyword}%"
            query = query.filter(
                or_(
                    User.username.ilike(keyword),
                    User.nickname.ilike(keyword),
                    User.email.ilike(keyword),
                )
            )

        users = query.order_by(User.created_at.desc()).all()
        return [_user_to_profile(u) for u in users]

    @staticmethod
    def get_admin_list(db: Session) -> list[dict]:
        """获取管理员列表（超级管理员）"""
        users = db.query(User).filter(User.role.in_(["admin", "super_admin"])).order_by(User.created_at.desc()).all()
        return [_user_to_profile(u) for u in users]

    @staticmethod
    def create_admin(db: Session, payload: dict) -> User:
        """创建管理员账号（超级管理员）"""
        existing = db.query(User).filter(
            or_(User.username == payload["username"], User.email == payload["email"])
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

        new_admin = User(
            username=payload["username"],
            email=payload["email"],
            hashed_password=hash_password(payload["password"]),
            nickname=payload.get("nickname", payload["username"]),
            phone=payload.get("phone"),
            role="admin",
            campus_role=payload.get("campus_role", "平台管理员"),
            bio="由总管理员创建的管理员账号。",
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        return new_admin

    @staticmethod
    def update_user_role(db: Session, user_id: int, role: str) -> User:
        """更新用户角色（超级管理员）"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if user.role == "super_admin":
            raise HTTPException(status_code=403, detail="不能修改超级管理员的角色")

        user.role = role
        if role == "admin":
            user.campus_role = "平台管理员"
        else:
            user.campus_role = "校园志愿者"
        db.commit()
        db.refresh(user)
        return user


user_service = UserService()