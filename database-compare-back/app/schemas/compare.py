"""比对任务相关Schema"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TableSelection(BaseModel):
    """表选择配置"""
    mode: str = Field(..., description="选择模式：all/include/exclude")
    tables: Optional[List[str]] = Field(None, description="表名列表")


class ColumnMapping(BaseModel):
    """字段映射"""
    source_column: str
    target_column: str


class TableMapping(BaseModel):
    """表映射配置"""
    source_table: str
    target_table: str
    column_mappings: Optional[List[ColumnMapping]] = None


class IncrementalConfig(BaseModel):
    """增量配置"""
    time_column: str = Field(..., description="时间字段名")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")


class StructureOptions(BaseModel):
    """结构比对选项"""
    compare_index: bool = Field(True, description="是否比对索引")
    compare_constraint: bool = Field(True, description="是否比对约束")
    compare_comment: bool = Field(True, description="是否比对注释")


class DataOptions(BaseModel):
    """数据比对选项"""
    float_precision: int = Field(6, description="浮点数精度")
    ignore_case: bool = Field(False, description="是否忽略大小写")
    trim_whitespace: bool = Field(True, description="是否忽略前后空格")
    datetime_precision: str = Field("second", description="时间精度：second/millisecond")
    skip_large_fields: bool = Field(True, description="是否跳过大字段")
    page_size: int = Field(10000, description="分页大小")


class CompareOptions(BaseModel):
    """比对选项"""
    mode: str = Field("full", description="比对模式：full/incremental")
    incremental_config: Optional[IncrementalConfig] = None
    structure_options: Optional[StructureOptions] = None
    data_options: Optional[DataOptions] = None
    table_mappings: Optional[List[TableMapping]] = None
    ignore_rules: Optional[List[str]] = Field(None, description="忽略规则ID列表")


class CreateTaskRequest(BaseModel):
    """创建比对任务请求"""
    source_id: str = Field(..., description="源数据源ID")
    target_id: str = Field(..., description="目标数据源ID")
    table_selection: TableSelection
    options: CompareOptions


class TaskProgress(BaseModel):
    """任务进度"""
    total_tables: int = 0
    completed_tables: int = 0
    current_table: Optional[str] = None
    current_phase: Optional[str] = None  # structure / data
    percentage: float = 0.0
    start_time: Optional[datetime] = None
    elapsed_seconds: int = 0
    estimated_remaining_seconds: Optional[int] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: Optional[TaskProgress] = None
    error_message: Optional[str] = None


class CreateTaskResponse(BaseModel):
    """创建任务响应"""
    task_id: str
    status: str
    created_at: datetime
