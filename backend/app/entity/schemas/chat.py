"""
对话模块 Schema
"""

from typing import Optional
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """创建会话请求"""

    title: Optional[str] = None


class SendMessageRequest(BaseModel):
    """发送消息请求体"""

    message: str = Field(..., min_length=1, max_length=10000, description="消息内容")


class SessionResponse(BaseModel):
    """会话响应"""

    id: int
    session_uuid: str
    title: Optional[str] = None

    model_config = {"from_attributes": True}
