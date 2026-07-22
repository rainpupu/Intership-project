from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.entity.db_models import (
    Cat,
    CatAuditRecord,
    CatIdentityEmbedding,
    CatObservation,
    CloudAdoptionOrder,
    RecognitionRecord,
    Role,
    User,
    UserRole,
)


DEFAULT_AVATAR = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=200&q=80"


def _user_to_profile(user: User) -> dict:
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


def _auth_error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


class UserService:
    @staticmethod
    def register(db: Session, phone: str, password: str) -> User:
        existing_user = db.query(User).filter(or_(User.phone == phone, User.username == phone)).first()
        if existing_user:
            raise _auth_error("PHONE_REGISTERED", "该手机号已经注册过，请直接登录", 409)

        new_user = User(
            username=phone,
            email=f"{phone}@pending.cattrace.local",
            phone=phone,
            hashed_password=hash_password(password),
            nickname="",
            avatar=DEFAULT_AVATAR,
            role="user",
            campus_role="校园志愿者",
            bio="关注校园流浪猫，希望帮助它们建立稳定档案。",
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        UserService._bind_role(db, new_user, "user")
        return new_user

    @staticmethod
    def login(db: Session, account: str, password: str) -> User:
        user = (
            db.query(User)
            .filter(or_(User.phone == account, User.username == account, User.email == account))
            .first()
        )
        if not user:
            raise _auth_error("PHONE_NOT_REGISTERED", "该手机号未注册账号，请先注册", 404)
        if not user.is_active:
            raise _auth_error("ACCOUNT_DISABLED", "账号已被禁用", 403)
        if not verify_password(password, user.hashed_password):
            raise _auth_error("INVALID_PASSWORD", "密码不正确，请重新输入", 401)

        user.last_login_at = datetime.now()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_access_token_for_user(user: User) -> str:
        return create_access_token(data={"sub": str(user.id)})

    @staticmethod
    def create_impersonation_token_for_user(target_user: User, operator: User) -> str:
        return create_access_token(
            data={
                "sub": str(target_user.id),
                "impersonated_by": str(operator.id),
                "purpose": "support_impersonation",
            }
        )

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
        return _user_to_profile(user)

    @staticmethod
    def update_profile(db: Session, user: User, payload: dict) -> User:
        user = db.merge(user)
        updatable_fields = ["nickname", "avatar", "email", "campus_role", "bio"]
        for field in updatable_fields:
            if field in payload and payload[field] is not None:
                setattr(user, field, payload[field])
        if "phone" in payload and payload["phone"] and payload["phone"] != user.phone:
            raise _auth_error("PHONE_IMMUTABLE", "手机号账号暂不支持在个人资料中修改", 400)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
        user = db.merge(user)
        if not verify_password(old_password, user.hashed_password):
            raise _auth_error("INVALID_OLD_PASSWORD", "旧密码错误", 400)
        user.hashed_password = hash_password(new_password)
        db.commit()

    @staticmethod
    def get_user_list(db: Session, role: Optional[str] = None, keyword: Optional[str] = None) -> list[dict]:
        query = db.query(User).filter(~User.username.like("virtual-admin-%"))
        if role and role != "all":
            query = query.filter(User.role == role)
        if keyword:
            keyword_like = f"%{keyword}%"
            query = query.filter(
                or_(
                    User.username.ilike(keyword_like),
                    User.phone.ilike(keyword_like),
                    User.nickname.ilike(keyword_like),
                    User.email.ilike(keyword_like),
                )
            )

        users = query.order_by(User.created_at.desc()).all()
        return [_user_to_profile(user) for user in users]

    @staticmethod
    def get_admin_list(db: Session) -> list[dict]:
        users = (
            db.query(User)
            .filter(User.role.in_(["admin", "super_admin"]))
            .order_by(User.created_at.desc())
            .all()
        )
        return [_user_to_profile(user) for user in users]

    @staticmethod
    def create_admin(db: Session, payload: dict) -> User:
        phone = payload["phone"]
        existing = db.query(User).filter(or_(User.phone == phone, User.username == phone, User.email == payload["email"])).first()
        if existing:
            raise _auth_error("ACCOUNT_EXISTS", "手机号或邮箱已存在", 409)

        new_admin = User(
            username=phone,
            phone=phone,
            email=payload["email"],
            hashed_password=hash_password(payload["password"]),
            nickname=payload.get("nickname", phone),
            avatar=DEFAULT_AVATAR,
            role="admin",
            campus_role=payload.get("campus_role", "平台管理员"),
            bio="由总管理员创建的管理员账号。",
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        UserService._bind_role(db, new_admin, "admin")
        return new_admin

    @staticmethod
    def update_user_role(db: Session, user_id: int, role: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if user.role == "super_admin":
            raise HTTPException(status_code=403, detail="不能修改超级管理员的角色")

        user.role = role
        user.campus_role = "平台管理员" if role == "admin" else "校园志愿者"
        db.commit()
        db.refresh(user)
        UserService._bind_role(db, user, role)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int, current_user: User) -> None:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="不能删除当前登录账号")
        if user.username.startswith("virtual-admin-"):
            raise HTTPException(status_code=400, detail="用户端视图账号不支持手动删除")
        if user.role == "super_admin":
            super_admin_count = db.query(User).filter(User.role == "super_admin").count()
            if super_admin_count <= 1:
                raise HTTPException(status_code=400, detail="至少需要保留一个总管理员账号")

        db.query(Cat).filter(Cat.created_by_id == user.id).update({Cat.created_by_id: None}, synchronize_session=False)
        db.query(CatObservation).filter(CatObservation.created_by_id == user.id).update(
            {CatObservation.created_by_id: None},
            synchronize_session=False,
        )
        db.query(CatAuditRecord).filter(CatAuditRecord.operator_id == user.id).update(
            {CatAuditRecord.operator_id: None},
            synchronize_session=False,
        )
        db.query(CatIdentityEmbedding).filter(CatIdentityEmbedding.created_by_id == user.id).update(
            {CatIdentityEmbedding.created_by_id: None},
            synchronize_session=False,
        )
        db.query(CloudAdoptionOrder).filter(CloudAdoptionOrder.user_id == user.id).update(
            {CloudAdoptionOrder.user_id: None},
            synchronize_session=False,
        )
        db.query(RecognitionRecord).filter(RecognitionRecord.user_id == user.id).delete(synchronize_session=False)
        db.query(UserRole).filter(UserRole.user_id == user.id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()

    @staticmethod
    def create_impersonation_session(db: Session, operator: User) -> dict:
        if operator.role not in ("admin", "super_admin"):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        target_user = UserService._get_or_create_virtual_user(db, operator)
        token = UserService.create_impersonation_token_for_user(target_user, operator)
        return {
            "token": token,
            "profile": _user_to_profile(target_user),
        }

    @staticmethod
    def _get_or_create_virtual_user(db: Session, operator: User) -> User:
        username = f"virtual-admin-{operator.id}"
        virtual_user = db.query(User).filter(User.username == username).first()
        nickname = f"{operator.nickname or operator.username}的用户端视图"
        email = f"virtual-admin-{operator.id}@cattrace.local"

        if virtual_user:
            virtual_user.nickname = nickname
            virtual_user.email = email
            virtual_user.avatar = operator.avatar or DEFAULT_AVATAR
            virtual_user.role = "user"
            virtual_user.campus_role = "校园志愿者"
            virtual_user.is_active = True
            db.commit()
            db.refresh(virtual_user)
            UserService._bind_role(db, virtual_user, "user")
            return virtual_user

        virtual_user = User(
            username=username,
            email=email,
            phone=None,
            hashed_password=hash_password(f"virtual-admin-{operator.id}-{datetime.now().timestamp()}"),
            nickname=nickname,
            avatar=operator.avatar or DEFAULT_AVATAR,
            role="user",
            campus_role="校园志愿者",
            bio="管理员用于排查用户端页面的专属虚拟用户账号。",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(virtual_user)
        db.commit()
        db.refresh(virtual_user)
        UserService._bind_role(db, virtual_user, "user")
        return virtual_user

    @staticmethod
    def _bind_role(db: Session, user: User, role_name: str) -> None:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            return

        stale_relations = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        for relation in stale_relations:
            if relation.role_id != role.id:
                db.delete(relation)

        existing = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).first()
        if not existing:
            db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()


user_service = UserService()
