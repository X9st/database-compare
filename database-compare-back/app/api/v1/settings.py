"""设置API"""
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.settings_service import SettingsService
from app.schemas.settings import (
    CreateIgnoreRuleRequest, UpdateIgnoreRuleRequest, ToggleRuleRequest,
    CreateTemplateRequest, UpdateTemplateRequest, CreateTaskFromTemplateRequest,
    UpdateSystemSettingsRequest, ExportConfigRequest
)
from app.schemas.common import Response

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> SettingsService:
    return SettingsService(db)


# ==================== 忽略规则 ====================

@router.get("/ignore-rules")
async def get_ignore_rules(
    service: SettingsService = Depends(get_service)
):
    """获取忽略规则列表"""
    data = service.get_ignore_rules()
    return Response(data=data)


@router.post("/ignore-rules")
async def create_ignore_rule(
    request: CreateIgnoreRuleRequest,
    service: SettingsService = Depends(get_service)
):
    """创建忽略规则"""
    data = service.create_ignore_rule(request)
    return Response(message="创建成功", data=data)


@router.put("/ignore-rules/{rule_id}")
async def update_ignore_rule(
    rule_id: str,
    request: UpdateIgnoreRuleRequest,
    service: SettingsService = Depends(get_service)
):
    """更新忽略规则"""
    data = service.update_ignore_rule(rule_id, request)
    if not data:
        raise HTTPException(status_code=404, detail="规则不存在")
    return Response(message="更新成功", data=data)


@router.delete("/ignore-rules/{rule_id}")
async def delete_ignore_rule(
    rule_id: str,
    service: SettingsService = Depends(get_service)
):
    """删除忽略规则"""
    if not service.delete_ignore_rule(rule_id):
        raise HTTPException(status_code=404, detail="规则不存在")
    return Response(message="删除成功")


@router.put("/ignore-rules/{rule_id}/toggle")
async def toggle_ignore_rule(
    rule_id: str,
    request: ToggleRuleRequest,
    service: SettingsService = Depends(get_service)
):
    """启用/禁用忽略规则"""
    if not service.toggle_ignore_rule(rule_id, request.enabled):
        raise HTTPException(status_code=404, detail="规则不存在")
    return Response(message="操作成功")


# ==================== 比对模板 ====================

@router.get("/templates")
async def get_templates(
    service: SettingsService = Depends(get_service)
):
    """获取模板列表"""
    data = service.get_templates()
    return Response(data=data)


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    service: SettingsService = Depends(get_service)
):
    """获取单个模板"""
    data = service.get_template(template_id)
    if not data:
        raise HTTPException(status_code=404, detail="模板不存在")
    return Response(data=data)


@router.post("/templates")
async def create_template(
    request: CreateTemplateRequest,
    service: SettingsService = Depends(get_service)
):
    """创建模板"""
    data = service.create_template(request)
    return Response(message="创建成功", data=data)


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    service: SettingsService = Depends(get_service)
):
    """更新模板"""
    data = service.update_template(template_id, request)
    if not data:
        raise HTTPException(status_code=404, detail="模板不存在")
    return Response(message="更新成功", data=data)


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    service: SettingsService = Depends(get_service)
):
    """删除模板"""
    if not service.delete_template(template_id):
        raise HTTPException(status_code=404, detail="模板不存在")
    return Response(message="删除成功")


@router.post("/templates/{template_id}/create-task")
async def create_task_from_template(
    template_id: str,
    request: CreateTaskFromTemplateRequest,
    service: SettingsService = Depends(get_service)
):
    """从模板创建任务"""
    try:
        data = service.create_task_from_template(template_id, request.override)
        return Response(message="任务创建成功", data=data)
    except ValueError as e:
        detail = str(e)
        if "模板不存在" in detail:
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)


# ==================== 系统设置 ====================

@router.get("/system")
async def get_system_settings(
    service: SettingsService = Depends(get_service)
):
    """获取系统设置"""
    data = service.get_system_settings()
    return Response(data=data)


@router.put("/system")
async def update_system_settings(
    request: UpdateSystemSettingsRequest,
    service: SettingsService = Depends(get_service)
):
    """更新系统设置"""
    data = service.update_system_settings(request)
    return Response(message="更新成功", data=data)


# ==================== 配置导入导出 ====================

@router.post("/export")
async def export_config(
    request: ExportConfigRequest,
    service: SettingsService = Depends(get_service)
):
    """导出配置"""
    data = service.export_config(request)
    return Response(message="导出成功", data=data)


@router.post("/import")
async def import_config(
    config_file: UploadFile = File(...),
    service: SettingsService = Depends(get_service)
):
    """导入配置"""
    try:
        content = await config_file.read()
        payload = json.loads(content.decode("utf-8"))
        data = service.import_config(payload)
        return Response(message="导入成功", data=data)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="配置文件必须是 UTF-8 编码的 JSON")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="配置文件不是合法 JSON")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
