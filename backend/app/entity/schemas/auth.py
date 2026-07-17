from __future__ import annotations

from datetime import datetime
from typing import Optional
import re

from pydantic import BaseModel, Field, field_validator


PHONE_PATTERN = r"^1[3-9]\d{9}$"
USER_CAMPUS_ROLES = {"校园志愿者", "社区志愿者", "喂养记录员", "领养意向人"}
ADMIN_CAMPUS_ROLES = {"平台管理员", "审核管理员", "猫咪档案管理员"}
ALL_CAMPUS_ROLES = USER_CAMPUS_ROLES | ADMIN_CAMPUS_ROLES


class UserRegister(BaseModel):
    phone: str = Field(..., description="手机号，作为登录账号")
    password: str = Field(..., min_length=6, max_length=100)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.match(PHONE_PATTERN, value):
            raise ValueError("请输入有效的 11 位手机号")
        return value


class UserLogin(BaseModel):
    username: str = Field(..., description="手机号账号")
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not re.match(PHONE_PATTERN, value) and value not in ("admin", "superadmin"):
            raise ValueError("请输入有效手机号")
        return value


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    campus_role: Optional[str] = Field(None, alias="campusRole")
    bio: Optional[str] = None

    model_config = {"populate_by_name": True}

    @field_validator("campus_role")
    @classmethod
    def validate_campus_role(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in ALL_CAMPUS_ROLES:
            raise ValueError("身份说明不在允许范围内")
        return value


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class CreateAdminRequest(BaseModel):
    phone: str = Field(..., description="管理员手机号账号")
    password: str = Field(..., min_length=6, max_length=100)
    nickname: str = Field(..., min_length=1, max_length=100)
    email: str
    campus_role: str = Field(default="平台管理员", alias="campusRole")

    model_config = {"populate_by_name": True}

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.match(PHONE_PATTERN, value):
            raise ValueError("请输入有效的 11 位手机号")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            raise ValueError("邮箱格式不正确")
        return value

    @field_validator("campus_role")
    @classmethod
    def validate_campus_role(cls, value: str) -> str:
        if value not in ADMIN_CAMPUS_ROLES:
            raise ValueError("管理员职责不在允许范围内")
        return value


class UpdateUserRoleRequest(BaseModel):
    user_id: int = Field(..., alias="userId")
    role: str

    model_config = {"populate_by_name": True}

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in ("user", "admin"):
            raise ValueError("角色只能是 user 或 admin")
        return value


class UserListQuery(BaseModel):
    role: Optional[str] = None
    keyword: Optional[str] = None


class UserProfileResponse(BaseModel):
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
    token: str
    profile: UserProfileResponse


class UserBrief(BaseModel):
    id: int
    username: str
    email: str
    avatar: Optional[str] = None
    roles: list[str] = []

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserBrief


class UserResponse(BaseModel):
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
    phone: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    is_system: bool
    permissions: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    display_name: str
    description: Optional[str] = None
    permission_codes: list[str] = []


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    module: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}
