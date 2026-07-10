"""
用户认证与权限相关 Schema
"""

from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    """用户注册请求"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, max_length=100, description="密码")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("邮箱格式不正确")
        return v


class UserLogin(BaseModel):
    """用户登录请求"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserBrief(BaseModel):
    """用户简要信息（嵌入在 Token 响应中）"""

    id: int
    username: str
    email: str
    avatar: Optional[str] = None
    roles: list[str] = []

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """登录成功响应"""

    access_token: str
    token_type: str = "bearer"
    user: UserBrief


class UserResponse(BaseModel):
    """用户详情响应"""

    id: int
    username: str
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool
    is_superuser: bool
    roles: list[str] = []
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
