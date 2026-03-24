"""数据源API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.datasource_service import DataSourceService
from app.schemas.datasource import (
    CreateDataSourceRequest, UpdateDataSourceRequest,
    TestConnectionRequest, CreateGroupRequest, UpdateGroupRequest
)
from app.schemas.common import Response

router = APIRouter()
group_router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> DataSourceService:
    return DataSourceService(db)


# ==================== 数据源接口 ====================

@router.get("")
async def get_datasources(
    group_id: Optional[str] = None,
    keyword: Optional[str] = None,
    db_type: Optional[str] = None,
    service: DataSourceService = Depends(get_service)
):
    """获取数据源列表"""
    data = service.get_list(group_id, keyword, db_type)
    return Response(data=data)


@router.get("/{ds_id}")
async def get_datasource(
    ds_id: str,
    service: DataSourceService = Depends(get_service)
):
    """获取单个数据源"""
    data = service.get_by_id(ds_id)
    if not data:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return Response(data=data)


@router.post("")
async def create_datasource(
    request: CreateDataSourceRequest,
    service: DataSourceService = Depends(get_service)
):
    """创建数据源"""
    data = service.create(request)
    return Response(message="创建成功", data=data)


@router.put("/{ds_id}")
async def update_datasource(
    ds_id: str,
    request: UpdateDataSourceRequest,
    service: DataSourceService = Depends(get_service)
):
    """更新数据源"""
    data = service.update(ds_id, request)
    if not data:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return Response(message="更新成功", data=data)


@router.delete("/{ds_id}")
async def delete_datasource(
    ds_id: str,
    service: DataSourceService = Depends(get_service)
):
    """删除数据源"""
    if not service.delete(ds_id):
        raise HTTPException(status_code=404, detail="数据源不存在")
    return Response(message="删除成功")


@router.post("/{ds_id}/test")
async def test_datasource_connection(
    ds_id: str,
    service: DataSourceService = Depends(get_service)
):
    """测试已保存数据源的连接"""
    data = service.test_connection_by_id(ds_id)
    return Response(data=data)


@router.post("/test-connection")
async def test_connection_direct(
    request: TestConnectionRequest,
    service: DataSourceService = Depends(get_service)
):
    """直接测试连接（不保存）"""
    data = service.test_connection_direct(request)
    return Response(data=data)


@router.post("/test")
async def test_connection_direct_alias(
    request: TestConnectionRequest,
    service: DataSourceService = Depends(get_service)
):
    """直接测试连接（不保存）- 别名"""
    data = service.test_connection_direct(request)
    return Response(data=data)


@router.get("/{ds_id}/tables")
async def get_tables(
    ds_id: str,
    schema: Optional[str] = None,
    service: DataSourceService = Depends(get_service)
):
    """获取表列表"""
    try:
        data = service.get_tables(ds_id, schema)
        return Response(data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{ds_id}/tables/{table_name}/schema")
async def get_table_schema(
    ds_id: str,
    table_name: str,
    service: DataSourceService = Depends(get_service)
):
    """获取表结构"""
    try:
        data = service.get_table_schema(ds_id, table_name)
        if not data:
            raise HTTPException(status_code=404, detail="数据源不存在")
        return Response(data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 分组接口 ====================

@group_router.get("")
async def get_groups(
    service: DataSourceService = Depends(get_service)
):
    """获取分组列表"""
    data = service.get_groups()
    return Response(data=data)


@group_router.post("")
async def create_group(
    request: CreateGroupRequest,
    service: DataSourceService = Depends(get_service)
):
    """创建分组"""
    data = service.create_group(request)
    return Response(message="创建成功", data=data)


@group_router.put("/{group_id}")
async def update_group(
    group_id: str,
    request: UpdateGroupRequest,
    service: DataSourceService = Depends(get_service)
):
    """更新分组"""
    data = service.update_group(group_id, request)
    if not data:
        raise HTTPException(status_code=404, detail="分组不存在")
    return Response(message="更新成功", data=data)


@group_router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    service: DataSourceService = Depends(get_service)
):
    """删除分组"""
    if not service.delete_group(group_id):
        raise HTTPException(status_code=404, detail="分组不存在")
    return Response(message="删除成功")
