"""结果服务"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import math

from app.models.datasource import DataSource
from app.models.compare_task import CompareTask, CompareResult, StructureDiff, DataDiff
from app.schemas.result import (
    CompareResultResponse, DataSourceSummary, ResultSummary,
    StructureDiffItem, DataDiffItem, TableCompareDetail
)
from app.schemas.common import PageInfo


class ResultService:
    """结果服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_result(self, result_id: str) -> Optional[CompareResultResponse]:
        """获取比对结果"""
        result = self.db.query(CompareResult).filter(
            CompareResult.id == result_id
        ).first()
        
        if not result:
            return None
        
        # 获取任务信息
        task = self.db.query(CompareTask).filter(
            CompareTask.id == result.task_id
        ).first()
        
        if not task:
            return None
        
        # 获取数据源信息
        source_ds = self.db.query(DataSource).filter(
            DataSource.id == task.source_id
        ).first()
        target_ds = self.db.query(DataSource).filter(
            DataSource.id == task.target_id
        ).first()
        
        # 计算耗时
        duration = None
        if task.started_at and task.completed_at:
            duration = int((task.completed_at - task.started_at).total_seconds())
        
        summary = result.summary or {}
        
        return CompareResultResponse(
            result_id=result.id,
            task_id=task.id,
            status=task.status,
            source_db=DataSourceSummary(
                id=source_ds.id,
                name=source_ds.name,
                db_type=source_ds.db_type
            ) if source_ds else None,
            target_db=DataSourceSummary(
                id=target_ds.id,
                name=target_ds.name,
                db_type=target_ds.db_type
            ) if target_ds else None,
            start_time=task.started_at,
            end_time=task.completed_at,
            duration_seconds=duration,
            summary=ResultSummary(
                total_tables=summary.get('total_tables', 0),
                structure_match_tables=summary.get('structure_match_tables', 0),
                structure_diff_tables=summary.get('structure_diff_tables', 0),
                data_match_tables=summary.get('data_match_tables', 0),
                data_diff_tables=summary.get('data_diff_tables', 0),
                total_structure_diffs=summary.get('total_structure_diffs', 0),
                total_data_diffs=summary.get('total_data_diffs', 0)
            )
        )
    
    def get_structure_diffs(self, result_id: str, table_name: str = None,
                            diff_type: str = None, page: int = 1, 
                            page_size: int = 20) -> tuple[List[StructureDiffItem], PageInfo]:
        """获取结构差异列表"""
        query = self.db.query(StructureDiff).filter(
            StructureDiff.result_id == result_id
        )
        
        if table_name:
            query = query.filter(StructureDiff.table_name == table_name)
        if diff_type:
            query = query.filter(StructureDiff.diff_type == diff_type)
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        diffs = query.offset(offset).limit(page_size).all()
        
        items = [StructureDiffItem(
            id=d.id,
            table_name=d.table_name,
            diff_type=d.diff_type,
            field_name=d.field_name,
            source_value=d.source_value,
            target_value=d.target_value,
            diff_detail=d.diff_detail
        ) for d in diffs]
        
        page_info = PageInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0
        )
        
        return items, page_info
    
    def get_data_diffs(self, result_id: str, table_name: str = None,
                       diff_type: str = None, page: int = 1,
                       page_size: int = 20) -> tuple[List[DataDiffItem], PageInfo]:
        """获取数据差异列表"""
        query = self.db.query(DataDiff).filter(
            DataDiff.result_id == result_id
        )
        
        if table_name:
            query = query.filter(DataDiff.table_name == table_name)
        if diff_type:
            query = query.filter(DataDiff.diff_type == diff_type)
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        diffs = query.offset(offset).limit(page_size).all()
        
        items = [DataDiffItem(
            id=d.id,
            table_name=d.table_name,
            primary_key=d.primary_key,
            diff_type=d.diff_type,
            diff_columns=d.diff_columns or [],
            source_values=d.source_values,
            target_values=d.target_values
        ) for d in diffs]
        
        page_info = PageInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0
        )
        
        return items, page_info
    
    def get_table_detail(self, result_id: str, table_name: str) -> Optional[TableCompareDetail]:
        """获取单表比对详情"""
        result = self.db.query(CompareResult).filter(
            CompareResult.id == result_id
        ).first()
        
        if not result:
            return None
        
        # 统计结构差异数
        structure_count = self.db.query(StructureDiff).filter(
            StructureDiff.result_id == result_id,
            StructureDiff.table_name == table_name
        ).count()
        
        # 统计数据差异数
        data_count = self.db.query(DataDiff).filter(
            DataDiff.result_id == result_id,
            DataDiff.table_name == table_name
        ).count()
        
        return TableCompareDetail(
            table_name=table_name,
            structure_match=structure_count == 0,
            data_match=data_count == 0,
            source_row_count=0,  # 需要额外查询
            target_row_count=0,
            structure_diffs_count=structure_count,
            data_diffs_count=data_count,
            compare_time_ms=0
        )
