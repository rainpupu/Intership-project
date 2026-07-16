"""
认证相关 API 路由
对齐前端 src/api/auth.ts 中的接口定义：
- POST /api/auth/login     — 登录
- POST /api/auth/register  — 注册
- GET  /api/auth/me        — 获取当前用户
- POST /api/auth/logout    — 登出
- PUT  /api/auth/profile   — 更新资料
- PUT  /api/auth/password  — 修改密码
- GET  /api/auth/users     — 用户列表（超级管理员）
- GET  /api/auth/admins    — 管理员列表（超级管理员）
- POST /api/auth/admins    — 创建管理员（超级管理员）
- PUT  /api/auth/users/{user_id}/role — 更新角色（超级管理员）
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.security import get_current_user
from app.database.session import get_db
from app.entity.db_models import User
from app.entity.schemas import (
    UserRegister,
    UserLogin,
    LoginResponse,
    UserProfileResponse,
    UpdateProfileRequest,
    ChangePassword,
    CreateAdminRequest,
    UpdateUserRoleRequest,
    UserListQuery,
    ApiResponse,
)
from app.services.user_service import user_service

router = APIRouter(prefix="/api/auth", tags=["认证"])


def _require_super_admin(current_user: User) -> None:
    """检查是否为超级管理员"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")


# ══════════════════════════════════════════════════════════════
# 注册 & 登录
# ══════════════════════════════════════════════════════════════

@router.post("/register", response_model=ApiResponse)
async def register(request: UserRegister, db: Session = Depends(get_db)):
    """用户注册 — 对齐前端 register(payload)"""
    user = user_service.register(
        db=db,
        username=request.username,
        password=request.password,
        nickname=request.nickname,
    )
    token = user_service.create_access_token_for_user(user)
    profile = user_service.get_user_profile(db, user)

    response_data = LoginResponse(token=token, profile=UserProfileResponse(**profile))
    return ApiResponse(data=response_data.model_dump(by_alias=True))


@router.post("/login", response_model=ApiResponse)
async def login(request: UserLogin, db: Session = Depends(get_db)):
    """用户登录 — 对齐前端 login(payload)"""
    user = user_service.login(db=db, username=request.username, password=request.password)
    token = user_service.create_access_token_for_user(user)
    profile = user_service.get_user_profile(db, user)

    response_data = LoginResponse(token=token, profile=UserProfileResponse(**profile))

    response = JSONResponse(
        content={"code": 200, "message": "success", "data": response_data.model_dump(by_alias=True)}
    )
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
    """登出"""
    response = JSONResponse(content={"code": 200, "message": "已登出", "data": None})
    response.delete_cookie(key="access_token", path="/")
    return response


# ══════════════════════════════════════════════════════════════
# 个人资料
# ══════════════════════════════════════════════════════════════

@router.get("/me", response_model=ApiResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户信息 — 对齐前端 getCurrentUser(token)"""
    profile = user_service.get_user_profile(db, current_user)
    return ApiResponse(data=UserProfileResponse(**profile).model_dump(by_alias=True))


@router.put("/profile", response_model=ApiResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户资料 — 对齐前端 updateUserProfile(profile, payload)"""
    user = user_service.update_profile(db, current_user, request.model_dump(exclude_none=True))
    profile = user_service.get_user_profile(db, user)
    return ApiResponse(data=UserProfileResponse(**profile).model_dump(by_alias=True))


@router.put("/password", response_model=ApiResponse)
async def change_password(
    request: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码"""
    user_service.change_password(db, current_user, request.old_password, request.new_password)
    return ApiResponse(message="密码修改成功")


# ══════════════════════════════════════════════════════════════
# 超级管理员 — 用户管理
# ══════════════════════════════════════════════════════════════

@router.get("/users", response_model=ApiResponse)
async def get_user_list(
    role: str = None,
    keyword: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户列表 — 对齐前端 getUserList(query)"""
    _require_super_admin(current_user)
    users = user_service.get_user_list(db, role=role, keyword=keyword)
    return ApiResponse(data=users)


@router.get("/admins", response_model=ApiResponse)
async def get_admin_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """管理员列表 — 对齐前端 getAdminList()"""
    _require_super_admin(current_user)
    admins = user_service.get_admin_list(db)
    return ApiResponse(data=admins)


@router.post("/admins", response_model=ApiResponse)
async def create_admin(
    request: CreateAdminRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建管理员 — 对齐前端 createAdmin(payload)"""
    _require_super_admin(current_user)
    admin = user_service.create_admin(db, request.model_dump(by_alias=True))
    profile = user_service.get_user_profile(db, admin)
    return ApiResponse(data=UserProfileResponse(**profile).model_dump(by_alias=True))


@router.put("/users/{user_id}/role", response_model=ApiResponse)
async def update_user_role(
    user_id: int,
    request: UpdateUserRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户角色 — 对齐前端 updateUserRole(payload)"""
    _require_super_admin(current_user)
    user = user_service.update_user_role(db, request.user_id, request.role)
    profile = user_service.get_user_profile(db, user)
    return ApiResponse(data=UserProfileResponse(**profile).model_dump(by_alias=True))