"""历史记录API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.history_service import HistoryService
from app.schemas.history import BatchDeleteRequest, CleanupRequest
from app.schemas.common import Response, PageResponse

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> HistoryService:
    return HistoryService(db)


@router.get("")
async def get_history(
    source_id: Optional[str] = None,
    target_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    service: HistoryService = Depends(get_service)
):
    """获取历史记录列表"""
    data, page_info = service.get_list(
        source_id, target_id, status, start_date, end_date, keyword, page, page_size
    )
    return PageResponse(data=data, page_info=page_info)


@router.delete("/{task_id}")
async def delete_history(
    task_id: str,
    service: HistoryService = Depends(get_service)
):
    """删除历史记录"""
    if not service.delete(task_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return Response(message="删除成功")


@router.post("/batch-delete")
async def batch_delete_history(
    request: BatchDeleteRequest,
    service: HistoryService = Depends(get_service)
):
    """批量删除历史记录"""
    deleted = service.batch_delete(request.task_ids)
    return Response(message=f"成功删除 {deleted} 条记录", data={"deleted": deleted})


@router.post("/cleanup")
async def cleanup_history(
    request: CleanupRequest,
    service: HistoryService = Depends(get_service)
):
    """清理历史记录"""
    deleted = service.cleanup(request.before_date, request.keep_count)
    return Response(message=f"成功清理 {deleted} 条记录", data={"deleted": deleted})
