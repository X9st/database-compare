"""历史记录服务"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, aliased
from sqlalchemy import or_
import json
import math

from app.models.datasource import DataSource
from app.models.compare_task import CompareTask, CompareResult, StructureDiff, DataDiff
from app.models.settings import SystemSetting
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
        source_alias = aliased(DataSource)
        target_alias = aliased(DataSource)
        query = (
            self.db.query(
                CompareTask,
                source_alias.id.label("source_db_id"),
                source_alias.name.label("source_db_name"),
                source_alias.db_type.label("source_db_type"),
                target_alias.id.label("target_db_id"),
                target_alias.name.label("target_db_name"),
                target_alias.db_type.label("target_db_type"),
            )
            .outerjoin(source_alias, CompareTask.source_id == source_alias.id)
            .outerjoin(target_alias, CompareTask.target_id == target_alias.id)
        )
        
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
        if keyword:
            keyword_like = f"%{keyword}%"
            query = query.filter(
                or_(
                    CompareTask.id.ilike(keyword_like),
                    source_alias.name.ilike(keyword_like),
                    target_alias.name.ilike(keyword_like),
                )
            )
        
        # 获取总数
        total = query.count()
        
        # 排序和分页
        query = query.order_by(CompareTask.created_at.desc())
        offset = (page - 1) * page_size
        rows = query.offset(offset).limit(page_size).all()
        
        items = []
        for row in rows:
            task = row[0]
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
                    id=row.source_db_id or task.source_id,
                    name=row.source_db_name or "未知",
                    db_type=row.source_db_type or "",
                ),
                target_db=DataSourceSummary(
                    id=row.target_db_id or task.target_id,
                    name=row.target_db_name or "未知",
                    db_type=row.target_db_type or "",
                ),
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
            before_dt = before_date
            if isinstance(before_date, str):
                try:
                    before_dt = datetime.fromisoformat(before_date)
                except ValueError:
                    before_dt = before_date
            # 删除指定日期之前的记录
            tasks = self.db.query(CompareTask).filter(
                CompareTask.created_at < before_dt
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

    def auto_cleanup_by_settings(self) -> int:
        """按系统设置自动清理历史记录"""
        enabled = self._read_setting("auto_cleanup_enabled", True)
        if not enabled:
            return 0

        retention_days = int(self._read_setting("history_retention_days", 90) or 90)
        history_max_count = int(self._read_setting("history_max_count", 500) or 500)

        before_date = None
        if retention_days > 0:
            before_date = (datetime.utcnow() - timedelta(days=retention_days)).isoformat()

        keep_count = history_max_count if history_max_count > 0 else None
        return self.cleanup(before_date=before_date, keep_count=keep_count)

    def _read_setting(self, key: str, default):
        row = self.db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not row:
            return default
        try:
            return json.loads(row.value)
        except Exception:
            return row.value
