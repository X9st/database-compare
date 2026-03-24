"""比对结果API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.result_service import ResultService
from app.schemas.result import ExportRequest
from app.schemas.common import Response, PageResponse

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> ResultService:
    return ResultService(db)


@router.get("/{result_id}")
async def get_result(
    result_id: str,
    service: ResultService = Depends(get_service)
):
    """获取比对结果"""
    data = service.get_result(result_id)
    if not data:
        raise HTTPException(status_code=404, detail="结果不存在")
    return Response(data=data)


@router.get("/{result_id}/structure-diffs")
async def get_structure_diffs(
    result_id: str,
    table_name: Optional[str] = None,
    diff_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    service: ResultService = Depends(get_service)
):
    """获取结构差异列表"""
    data, page_info = service.get_structure_diffs(
        result_id, table_name, diff_type, page, page_size
    )
    return PageResponse(data=data, page_info=page_info)


@router.get("/{result_id}/data-diffs")
async def get_data_diffs(
    result_id: str,
    table_name: Optional[str] = None,
    diff_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    service: ResultService = Depends(get_service)
):
    """获取数据差异列表"""
    data, page_info = service.get_data_diffs(
        result_id, table_name, diff_type, page, page_size
    )
    return PageResponse(data=data, page_info=page_info)


@router.get("/{result_id}/tables/{table_name}")
async def get_table_detail(
    result_id: str,
    table_name: str,
    service: ResultService = Depends(get_service)
):
    """获取单表比对详情"""
    data = service.get_table_detail(result_id, table_name)
    if not data:
        raise HTTPException(status_code=404, detail="结果不存在")
    return Response(data=data)


@router.post("/{result_id}/export")
async def export_result(
    result_id: str,
    request: ExportRequest,
    service: ResultService = Depends(get_service)
):
    """导出比对报告"""
    # TODO: 实现导出功能
    return Response(
        message="导出成功",
        data={
            "file_path": f"/data/exports/report_{result_id}.xlsx",
            "file_name": f"比对报告_{result_id}.xlsx",
            "file_size": 0,
            "download_url": f"/api/v1/files/download/report_{result_id}.xlsx"
        }
    )
