"""
通用 Schema 模型
"""

from typing import Optional, Union
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """统一 API 响应"""

    code: int = 200
    message: str = "success"
    data: Optional[Union[dict, list]] = None


class PageParams(BaseModel):
    """分页查询参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PageResponse(BaseModel):
    """分页响应"""

    total: int
    page: int
    page_size: int
    total_pages: int
    items: list
