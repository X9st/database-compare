"""比对结果相关Schema"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DataSourceSummary(BaseModel):
    """数据源摘要"""
    id: str
    name: str
    db_type: str


class ResultSummary(BaseModel):
    """结果汇总"""
    total_tables: int
    structure_match_tables: int
    structure_diff_tables: int
    data_match_tables: int
    data_diff_tables: int
    no_diff_tables: int = 0
    total_structure_diffs: int
    total_data_diffs: int
    structure_diff_type_counts: Dict[str, int] = Field(default_factory=dict)
    data_diff_type_counts: Dict[str, int] = Field(default_factory=dict)


class CompareResultResponse(BaseModel):
    """比对结果响应"""
    result_id: str
    task_id: str
    status: str
    source_db: DataSourceSummary
    target_db: DataSourceSummary
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    summary: ResultSummary


class StructureDiffItem(BaseModel):
    """结构差异项"""
    id: str
    table_name: str
    diff_type: str
    field_name: Optional[str] = None
    source_value: Optional[str] = None
    target_value: Optional[str] = None
    diff_detail: Optional[str] = None


class DataDiffItem(BaseModel):
    """数据差异项"""
    id: str
    table_name: str
    primary_key: Dict[str, Any]
    diff_type: str
    diff_columns: List[str]
    source_values: Optional[Dict[str, Any]] = None
    target_values: Optional[Dict[str, Any]] = None


class TableCompareDetail(BaseModel):
    """单表比对详情"""
    table_name: str
    structure_match: bool
    data_match: bool
    source_row_count: int
    target_row_count: int
    structure_diffs_count: int
    data_diffs_count: int
    compare_time_ms: int


class ExportOptions(BaseModel):
    """导出选项"""
    include_structure_diffs: bool = True
    include_data_diffs: bool = True
    max_data_diffs: int = 1000
    tables: Optional[List[str]] = None


class ExportRequest(BaseModel):
    """导出请求"""
    format: str = Field(..., description="导出格式：excel/html/txt")
    options: Optional[ExportOptions] = None


class ExportResponse(BaseModel):
    """导出响应"""
    file_path: str
    file_name: str
    file_size: int
    download_url: str


class ResultCompareRequest(BaseModel):
    """结果对比请求"""
    baseline_result_id: str
    current_result_id: str


class ResultCompareExportRequest(ResultCompareRequest):
    """结果对比导出请求"""
    format: str = Field("txt", description="导出格式：txt/html/excel")


class DiffCompareGroup(BaseModel):
    """差异分组"""
    structure: List[StructureDiffItem] = Field(default_factory=list)
    data: List[DataDiffItem] = Field(default_factory=list)


class ResultCompareSummary(BaseModel):
    """结果对比汇总"""
    added: int = 0
    resolved: int = 0
    unchanged: int = 0
    added_structure: int = 0
    added_data: int = 0
    resolved_structure: int = 0
    resolved_data: int = 0
    unchanged_structure: int = 0
    unchanged_data: int = 0


class ResultCompareResponse(BaseModel):
    """结果对比响应"""
    baseline_result_id: str
    current_result_id: str
    summary: ResultCompareSummary
    added: DiffCompareGroup
    resolved: DiffCompareGroup
    unchanged: DiffCompareGroup
