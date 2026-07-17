"""
用户认证与权限相关 Schema
对齐前端 src/types/user.ts 中的类型定义
"""
from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator


# ══════════════════════════════════════════════════════════════
# 请求 Schema
# ══════════════════════════════════════════════════════════════

class UserRegister(BaseModel):
    """用户注册请求 — 对齐前端 RegisterPayload"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    nickname: str = Field(..., min_length=1, max_length=100, description="昵称")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v


class UserLogin(BaseModel):
    """用户登录请求 — 对齐前端 LoginPayload"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UpdateProfileRequest(BaseModel):
    """更新用户资料 — 对齐前端 UpdateProfilePayload"""
    nickname: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像 URL")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    campus_role: Optional[str] = Field(None, alias="campusRole", description="校园角色")
    bio: Optional[str] = Field(None, description="个人简介")

    model_config = {"populate_by_name": True}


class ChangePassword(BaseModel):
    """修改密码"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class CreateAdminRequest(BaseModel):
    """创建管理员 — 对齐前端 CreateAdminPayload"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    nickname: str = Field(..., min_length=1, max_length=100, description="昵称")
    email: str = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    campus_role: str = Field(..., alias="campusRole", description="校园角色")

    model_config = {"populate_by_name": True}

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("邮箱格式不正确")
        return v


class UpdateUserRoleRequest(BaseModel):
    """更新用户角色 — 对齐前端 UpdateUserRolePayload"""
    user_id: int = Field(..., alias="userId", description="用户 ID")
    role: str = Field(..., description="目标角色：user 或 admin")

    model_config = {"populate_by_name": True}

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "admin"):
            raise ValueError("角色只能是 user 或 admin")
        return v


class UserListQuery(BaseModel):
    """用户列表查询 — 对齐前端 UserListQuery"""
    role: Optional[str] = Field(None, description="角色筛选：user/admin/super_admin/all")
    keyword: Optional[str] = Field(None, description="搜索关键词（用户名/昵称/邮箱）")


# ══════════════════════════════════════════════════════════════
# 响应 Schema
# ══════════════════════════════════════════════════════════════

class UserProfileResponse(BaseModel):
    """用户信息响应 — 对齐前端 UserProfile"""
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    role: str = "user"
    email: str
    phone: Optional[str] = None
    campus_role: Optional[str] = Field(None, alias="campusRole")
    bio: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class LoginResponse(BaseModel):
    """登录响应 — 对齐前端 AuthResult"""
    token: str
    profile: UserProfileResponse


class UserBrief(BaseModel):
    """用户简要信息（嵌入在 Token 响应中，兼容旧版）"""
    id: int
    username: str
    email: str
    avatar: Optional[str] = None
    roles: list[str] = []

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """登录成功响应（兼容旧版）"""
    access_token: str
    token_type: str = "bearer"
    user: UserBrief


class UserResponse(BaseModel):
    """用户详情响应（兼容旧版）"""
    id: int
    username: str
    email: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role: str = "user"
    campus_role: Optional[str] = Field(None, alias="campusRole")
    bio: Optional[str] = None
    is_active: bool
    is_superuser: bool
    roles: list[str] = []
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class UserUpdate(BaseModel):
    """用户信息更新（兼容旧版）"""
    phone: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None


# ══════════════════════════════════════════════════════════════
# 角色权限 Schema（保留兼容）
# ══════════════════════════════════════════════════════════════

class RoleResponse(BaseModel):
    """角色响应"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    is_system: bool
    permissions: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    """创建角色"""
    name: str = Field(..., min_length=2, max_length=50, description="角色标识")
    display_name: str = Field(..., description="角色显示名")
    description: Optional[str] = None
    permission_codes: list[str] = Field(default=[], description="权限编码列表")


class PermissionResponse(BaseModel):
    """权限响应"""
    id: int
    code: str
    name: str
    module: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}