"""历史记录服务"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import math

from app.models.datasource import DataSource
from app.models.compare_task import CompareTask, CompareResult, StructureDiff, DataDiff
from app.schemas.history import HistoryItem
from app.schemas.result import DataSourceSummary
from app.schemas.common import PageInfo


class HistoryService:
    """历史记录服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_list(self, source_id: str = None, target_id: str = None,
                 status: str = None, start_date: str = None,
                 end_date: str = None, keyword: str = None,
                 page: int = 1, page_size: int = 20) -> tuple[List[HistoryItem], PageInfo]:
        """获取历史记录列表"""
        query = self.db.query(CompareTask)
        
        if source_id:
            query = query.filter(CompareTask.source_id == source_id)
        if target_id:
            query = query.filter(CompareTask.target_id == target_id)
        if status:
            query = query.filter(CompareTask.status == status)
        if start_date:
            query = query.filter(CompareTask.created_at >= start_date)
        if end_date:
            query = query.filter(CompareTask.created_at <= end_date)
        
        # 获取总数
        total = query.count()
        
        # 排序和分页
        query = query.order_by(CompareTask.created_at.desc())
        offset = (page - 1) * page_size
        tasks = query.offset(offset).limit(page_size).all()
        
        items = []
        for task in tasks:
            # 获取数据源信息
            source_ds = self.db.query(DataSource).filter(
                DataSource.id == task.source_id
            ).first()
            target_ds = self.db.query(DataSource).filter(
                DataSource.id == task.target_id
            ).first()
            
            # 获取结果信息
            result = self.db.query(CompareResult).filter(
                CompareResult.task_id == task.id
            ).first()
            
            result_id = None
            has_diff = False
            structure_diffs_count = 0
            data_diffs_count = 0
            table_count = 0
            
            if result:
                result_id = result.id
                summary = result.summary or {}
                structure_diffs_count = summary.get('total_structure_diffs', 0)
                data_diffs_count = summary.get('total_data_diffs', 0)
                table_count = summary.get('total_tables', 0)
                has_diff = structure_diffs_count > 0 or data_diffs_count > 0
            
            # 计算耗时
            duration = None
            if task.started_at and task.completed_at:
                duration = int((task.completed_at - task.started_at).total_seconds())
            
            items.append(HistoryItem(
                task_id=task.id,
                result_id=result_id,
                source_db=DataSourceSummary(
                    id=source_ds.id,
                    name=source_ds.name,
                    db_type=source_ds.db_type
                ) if source_ds else DataSourceSummary(id="", name="未知", db_type=""),
                target_db=DataSourceSummary(
                    id=target_ds.id,
                    name=target_ds.name,
                    db_type=target_ds.db_type
                ) if target_ds else DataSourceSummary(id="", name="未知", db_type=""),
                status=task.status,
                table_count=table_count,
                has_diff=has_diff,
                structure_diffs_count=structure_diffs_count,
                data_diffs_count=data_diffs_count,
                created_at=task.created_at,
                duration_seconds=duration
            ))
        
        page_info = PageInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0
        )
        
        return items, page_info
    
    def delete(self, task_id: str) -> bool:
        """删除历史记录"""
        task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if not task:
            return False
        
        # 删除关联的结果和差异
        result = self.db.query(CompareResult).filter(
            CompareResult.task_id == task_id
        ).first()
        
        if result:
            self.db.query(StructureDiff).filter(
                StructureDiff.result_id == result.id
            ).delete()
            self.db.query(DataDiff).filter(
                DataDiff.result_id == result.id
            ).delete()
            self.db.delete(result)
        
        self.db.delete(task)
        self.db.commit()
        return True
    
    def batch_delete(self, task_ids: List[str]) -> int:
        """批量删除历史记录"""
        deleted = 0
        for task_id in task_ids:
            if self.delete(task_id):
                deleted += 1
        return deleted
    
    def cleanup(self, before_date: str = None, keep_count: int = None) -> int:
        """清理历史记录"""
        deleted = 0
        
        if before_date:
            # 删除指定日期之前的记录
            tasks = self.db.query(CompareTask).filter(
                CompareTask.created_at < before_date
            ).all()
            for task in tasks:
                if self.delete(task.id):
                    deleted += 1
        
        if keep_count:
            # 只保留最近N条记录
            total = self.db.query(CompareTask).count()
            if total > keep_count:
                # 获取需要删除的记录
                tasks = self.db.query(CompareTask).order_by(
                    CompareTask.created_at.desc()
                ).offset(keep_count).all()
                for task in tasks:
                    if self.delete(task.id):
                        deleted += 1
        
        return deleted
