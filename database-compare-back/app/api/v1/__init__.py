"""API v1路由汇总"""
from fastapi import APIRouter
from app.api.v1 import datasource, compare, result, history, settings, files

router = APIRouter()

# 注册各模块路由
router.include_router(datasource.router, prefix="/datasources", tags=["数据源"])
router.include_router(datasource.group_router, prefix="/datasource-groups", tags=["数据源分组"])
router.include_router(compare.router, prefix="/compare", tags=["比对任务"])
router.include_router(result.router, prefix="/compare/results", tags=["比对结果"])
router.include_router(history.router, prefix="/history", tags=["历史记录"])
router.include_router(settings.router, prefix="/settings", tags=["设置"])
router.include_router(files.router, prefix="/files", tags=["文件"])
