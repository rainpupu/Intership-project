"""
通用 Schema 模型
"""

from typing import Optional, Union
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一 API 响应"""

    code: int = 200
    message: str = "success"
    data: Optional[Union[dict, list]] = None
