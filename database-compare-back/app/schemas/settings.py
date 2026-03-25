"""设置相关Schema"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# 忽略规则
class IgnoreRuleBase(BaseModel):
    """忽略规则基础字段"""
    name: str = Field(..., max_length=100)
    rule_type: str = Field(..., description="规则类型：column/dataType/diffType/table")
    pattern: str = Field(..., description="匹配模式")
    tables: Optional[List[str]] = Field(None, description="适用的表列表")
    enabled: bool = Field(True)


class CreateIgnoreRuleRequest(IgnoreRuleBase):
    """创建忽略规则请求"""
    pass


class UpdateIgnoreRuleRequest(BaseModel):
    """更新忽略规则请求"""
    name: Optional[str] = Field(None, max_length=100)
    rule_type: Optional[str] = None
    pattern: Optional[str] = None
    tables: Optional[List[str]] = None
    enabled: Optional[bool] = None


class IgnoreRuleResponse(IgnoreRuleBase):
    """忽略规则响应"""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ToggleRuleRequest(BaseModel):
    """启用/禁用规则请求"""
    enabled: bool


# 比对模板
class TemplateConfig(BaseModel):
    """模板配置"""
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    table_selection: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None


class CreateTemplateRequest(BaseModel):
    """创建模板请求"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    config: TemplateConfig


class UpdateTemplateRequest(BaseModel):
    """更新模板请求"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    config: Optional[TemplateConfig] = None


class TemplateResponse(BaseModel):
    """模板响应"""
    id: str
    name: str
    description: Optional[str] = None
    config: TemplateConfig
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CreateTaskFromTemplateRequest(BaseModel):
    """从模板创建任务请求"""
    override: Optional[Dict[str, Any]] = None


# 系统设置
class SystemSettings(BaseModel):
    """系统设置"""
    compare_thread_count: int = Field(4, description="比对线程数")
    db_query_timeout: int = Field(60, description="数据库查询超时秒数")
    compare_timeout: int = Field(3600, description="比对超时秒数")
    history_retention_days: int = Field(90, description="历史记录保留天数")
    history_max_count: int = Field(500, description="历史记录最大数量")
    default_page_size: int = Field(10000, description="默认分页大小")
    max_diff_display: int = Field(1000, description="差异最大显示数量")
    auto_cleanup_enabled: bool = Field(True, description="是否启用自动清理")


class UpdateSystemSettingsRequest(BaseModel):
    """更新系统设置请求"""
    compare_thread_count: Optional[int] = None
    db_query_timeout: Optional[int] = None
    compare_timeout: Optional[int] = None
    history_retention_days: Optional[int] = None
    history_max_count: Optional[int] = None
    default_page_size: Optional[int] = None
    max_diff_display: Optional[int] = None
    auto_cleanup_enabled: Optional[bool] = None


# 配置导入导出
class ExportConfigRequest(BaseModel):
    """导出配置请求"""
    include_datasources: bool = True
    include_templates: bool = True
    include_rules: bool = True
    include_system_settings: bool = True


class ImportConfigResponse(BaseModel):
    """导入配置响应"""
    datasource_groups_imported: int = 0
    datasources_imported: int = 0
    templates_imported: int = 0
    rules_imported: int = 0
    system_settings_imported: int = 0
