"""
通用响应模型
"""
from typing import Any, Optional, List
from pydantic import BaseModel


class BaseResponse(BaseModel):
    """统一响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None


class PaginatedData(BaseModel):
    """分页数据"""
    list: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
