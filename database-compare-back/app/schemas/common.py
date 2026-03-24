"""通用响应模型"""
from typing import TypeVar, Generic, Optional, Any, List
from pydantic import BaseModel

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """通用响应模型"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class PageInfo(BaseModel):
    """分页信息"""
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0


class PageResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    code: int = 0
    message: str = "success"
    data: Optional[List[T]] = None
    page_info: Optional[PageInfo] = None


# 错误码定义
class ErrorCode:
    SUCCESS = 0
    PARAM_ERROR = 1001
    NOT_FOUND = 1002
    ALREADY_EXISTS = 1003
    DB_CONNECTION_FAILED = 2001
    DB_QUERY_FAILED = 2002
    DB_PERMISSION_DENIED = 2003
    TASK_NOT_FOUND = 3001
    TASK_EXECUTION_FAILED = 3002
    TASK_CANCELLED = 3003
    SYSTEM_ERROR = 9999
