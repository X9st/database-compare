"""启动维护服务"""
from __future__ import annotations

from typing import Dict, List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.compare_task import CompareTask, CompareResult, StructureDiff, DataDiff
from app.models.datasource import DataSource
from app.models.settings import CompareTemplate


class MaintenanceService:
    """启动阶段一次性维护任务。"""

    LEGACY_DB_TYPES = {"sqlserver", "postgresql"}

    def __init__(self, db: Session):
        self.db = db

    def cleanup_legacy_datasources(self) -> Dict[str, int]:
        """清理已下线类型数据源及其关联历史。"""
        legacy_sources: List[DataSource] = (
            self.db.query(DataSource)
            .filter(DataSource.db_type.in_(self.LEGACY_DB_TYPES))
            .all()
        )
        if not legacy_sources:
            return {
                "datasources_deleted": 0,
                "tasks_deleted": 0,
                "results_deleted": 0,
                "structure_diffs_deleted": 0,
                "data_diffs_deleted": 0,
                "templates_deleted": 0,
            }

        ds_ids = [item.id for item in legacy_sources]

        tasks = (
            self.db.query(CompareTask)
            .filter(or_(CompareTask.source_id.in_(ds_ids), CompareTask.target_id.in_(ds_ids)))
            .all()
        )
        task_ids = [item.id for item in tasks]

        result_ids: List[str] = []
        if task_ids:
            result_ids = [
                item.id
                for item in self.db.query(CompareResult).filter(CompareResult.task_id.in_(task_ids)).all()
            ]

        structure_diffs_deleted = 0
        data_diffs_deleted = 0
        results_deleted = 0
        tasks_deleted = 0
        if result_ids:
            structure_diffs_deleted = (
                self.db.query(StructureDiff).filter(StructureDiff.result_id.in_(result_ids)).delete(synchronize_session=False)
            )
            data_diffs_deleted = (
                self.db.query(DataDiff).filter(DataDiff.result_id.in_(result_ids)).delete(synchronize_session=False)
            )
            results_deleted = (
                self.db.query(CompareResult).filter(CompareResult.id.in_(result_ids)).delete(synchronize_session=False)
            )
        if task_ids:
            tasks_deleted = (
                self.db.query(CompareTask).filter(CompareTask.id.in_(task_ids)).delete(synchronize_session=False)
            )

        templates_deleted = 0
        templates = self.db.query(CompareTemplate).all()
        for template in templates:
            config = template.config or {}
            if config.get("source_id") in ds_ids or config.get("target_id") in ds_ids:
                self.db.delete(template)
                templates_deleted += 1

        datasources_deleted = (
            self.db.query(DataSource).filter(DataSource.id.in_(ds_ids)).delete(synchronize_session=False)
        )
        self.db.commit()

        return {
            "datasources_deleted": int(datasources_deleted or 0),
            "tasks_deleted": int(tasks_deleted or 0),
            "results_deleted": int(results_deleted or 0),
            "structure_diffs_deleted": int(structure_diffs_deleted or 0),
            "data_diffs_deleted": int(data_diffs_deleted or 0),
            "templates_deleted": int(templates_deleted or 0),
        }
