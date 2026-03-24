"""历史记录相关Schema"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.schemas.result import DataSourceSummary


class HistoryItem(BaseModel):
    """历史记录项"""
    task_id: str
    result_id: Optional[str] = None
    source_db: DataSourceSummary
    target_db: DataSourceSummary
    status: str
    table_count: int
    has_diff: bool
    structure_diffs_count: int
    data_diffs_count: int
    created_at: datetime
    duration_seconds: Optional[int] = None


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    task_ids: List[str]


class CleanupRequest(BaseModel):
    """清理请求"""
    before_date: Optional[str] = None
    keep_count: Optional[int] = None
