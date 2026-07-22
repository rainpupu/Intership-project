from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.security import get_current_user
from app.database.session import get_db
from app.entity.db_models import User
from app.entity.schemas import (
    ApiResponse,
    ChangePassword,
    CreateAdminRequest,
    LoginResponse,
    UpdateProfileRequest,
    UpdateUserRoleRequest,
    UserLogin,
    UserProfileResponse,
    UserRegister,
)
from app.services.user_service import user_service


router = APIRouter(prefix="/api/auth", tags=["认证"])


def _require_super_admin(current_user: User) -> None:
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")


@router.post("/register", response_model=ApiResponse)
async def register(request: UserRegister, db: Session = Depends(get_db)):
    user = user_service.register(
        db=db,
        phone=request.phone,
        password=request.password,
    )
    token = user_service.create_access_token_for_user(user)
    profile = user_service.get_user_profile(db, user)
    data = LoginResponse(token=token, profile=UserProfileResponse(**profile))
    response = JSONResponse(content={"code": 200, "message": "success", "data": data.model_dump(by_alias=True)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/login")
async def login(request: UserLogin, db: Session = Depends(get_db)):
    user = user_service.login(db=db, account=request.username, password=request.password)
    token = user_service.create_access_token_for_user(user)
    profile = user_service.get_user_profile(db, user)
    data = LoginResponse(token=token, profile=UserProfileResponse(**profile))

    response = JSONResponse(content={"code": 200, "message": "success", "data": data.model_dump(by_alias=True)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"code": 200, "message": "已登出", "data": None})
    response.delete_cookie(key="access_token", path="/")
    return response


@router.get("/me", response_model=ApiResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = user_service.get_user_profile(db, current_user)
    return ApiResponse(data=UserProfileResponse(**profile).model_dump(by_alias=True))


@router.put("/profile", response_model=ApiResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = user_service.update_profile(db, current_user, request.model_dump(exclude_none=True))
    profile = user_service.get_user_profile(db, user)
    return ApiResponse(data=UserProfileResponse(**profile).model_dump(by_alias=True))


@router.put("/password", response_model=ApiResponse)
async def change_password(
    request: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_service.change_password(db, current_user, request.old_password, request.new_password)
    return ApiResponse(message="密码修改成功")


@router.get("/users", response_model=ApiResponse)
async def get_user_list(
    role: str | None = None,
    keyword: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(current_user)
    return ApiResponse(data=user_service.get_user_list(db, role=role, keyword=keyword))


@router.get("/admins", response_model=ApiResponse)
async def get_admin_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(current_user)
    return ApiResponse(data=user_service.get_admin_list(db))


@router.post("/admins", response_model=ApiResponse)
async def create_admin(
    request: CreateAdminRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(current_user)
    admin = user_service.create_admin(db, request.model_dump())
    profile = user_service.get_user_profile(db, admin)
    return ApiResponse(data=UserProfileResponse(**profile).model_dump(by_alias=True))


@router.put("/users/{user_id}/role", response_model=ApiResponse)
async def update_user_role(
    user_id: int,
    request: UpdateUserRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(current_user)
    user = user_service.update_user_role(db, request.user_id or user_id, request.role)
    profile = user_service.get_user_profile(db, user)
    return ApiResponse(data=UserProfileResponse(**profile).model_dump(by_alias=True))


@router.delete("/users/{user_id}", response_model=ApiResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(current_user)
    user_service.delete_user(db, user_id, current_user)
    return ApiResponse(data={"success": True}, message="账号已删除")


@router.post("/impersonation/self", response_model=ApiResponse)
async def create_self_impersonation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = user_service.create_impersonation_session(db, current_user)
    data = LoginResponse(
        token=session["token"],
        profile=UserProfileResponse(**session["profile"]),
    )
    return ApiResponse(data=data.model_dump(by_alias=True), message="用户端视图会话已创建")
