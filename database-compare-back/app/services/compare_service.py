"""比对服务"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import fnmatch
import hashlib
import json
import uuid

from sqlalchemy.orm import Session
from loguru import logger

from app.models.datasource import DataSource
from app.models.compare_task import CompareTask, CompareResult, StructureDiff, DataDiff as DataDiffModel
from app.models.settings import IgnoreRule, SystemSetting
from app.schemas.compare import CreateTaskRequest, TaskProgress, TaskStatusResponse
from app.core.connector import ConnectorFactory
from app.core.comparator.structure import StructureComparator, StructureDiff as ComparatorStructureDiff
from app.core.comparator.data import (
    DataComparator,
    DataDiff as ComparatorDataDiff,
    DataDiffType,
)
from app.core.task.manager import TaskManager, TaskStatus
from app.services.history_service import HistoryService
from app.utils.crypto import decrypt


class CompareService:
    """比对服务"""

    def __init__(self, db: Session):
        self.db = db
        self.task_manager = TaskManager()

    def create_task(self, request: CreateTaskRequest) -> Dict[str, Any]:
        """创建比对任务"""
        source_ds = self.db.query(DataSource).filter(DataSource.id == request.source_id).first()
        target_ds = self.db.query(DataSource).filter(DataSource.id == request.target_id).first()

        if not source_ds:
            raise ValueError(f"源数据源不存在: {request.source_id}")
        if not target_ds:
            raise ValueError(f"目标数据源不存在: {request.target_id}")

        config_data = request.model_dump()
        self._validate_incremental_config(config_data)
        if config_data.get("table_selection", {}).get("mode") == "mapping":
            self._validate_mapping_task_config(source_ds, target_ds, config_data)

        # 元信息和断点续比信息
        config_hash = self._compute_config_hash(config_data)
        config_data.setdefault("_meta", {})["config_hash"] = config_hash
        options = (config_data.get("options") or {})
        resume_enabled = bool(options.get("resume_from_checkpoint", True))
        resume_payload = None
        if resume_enabled:
            resume_payload = self._prepare_resume_from_checkpoint(
                source_id=request.source_id,
                target_id=request.target_id,
                config_hash=config_hash,
            )
        if resume_payload:
            config_data["_resume"] = resume_payload

        task = CompareTask(
            id=str(uuid.uuid4()),
            source_id=request.source_id,
            target_id=request.target_id,
            status="pending",
            config=config_data,
        )

        self.db.add(task)
        self.db.commit()

        self.task_manager.create_task(task_id=task.id)

        return {
            "task_id": task.id,
            "status": "pending",
            "created_at": task.created_at,
            "resume_from_task_id": (config_data.get("_resume") or {}).get("from_task_id"),
        }

    async def start_task(self, task_id: str) -> Dict[str, Any]:
        """启动比对任务"""
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if not db_task:
            raise ValueError("任务不存在")

        if db_task.status not in ["pending", "paused"]:
            raise ValueError(f"任务状态 {db_task.status} 不允许启动")

        self.task_manager.ensure_task(task_id)

        db_task.status = "running"
        db_task.started_at = datetime.utcnow()
        self.db.commit()

        asyncio.create_task(self._execute_compare(task_id))

        return {"task_id": task_id, "status": "running"}

    async def _execute_compare(self, task_id: str) -> None:
        """执行比对（异步）"""
        runtime_settings = self._get_runtime_settings()
        compare_timeout = int(runtime_settings.get("compare_timeout", 3600))

        try:
            if compare_timeout > 0:
                await asyncio.wait_for(
                    self._run_compare(task_id=task_id, runtime_settings=runtime_settings),
                    timeout=compare_timeout,
                )
            else:
                await self._run_compare(task_id=task_id, runtime_settings=runtime_settings)
        except asyncio.TimeoutError:
            logger.error(f"任务 {task_id} 执行超时")
            self._mark_task_failed(task_id, "比对任务执行超时，请调整 compare_timeout 后重试")
        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {e}")
            self._mark_task_failed(task_id, str(e))

    async def _run_compare(self, task_id: str, runtime_settings: Dict[str, Any]) -> None:
        self.task_manager.ensure_task(task_id)
        self.task_manager.update_status(task_id, TaskStatus.RUNNING)
        self._update_task_progress(task_id, start_time=datetime.utcnow())

        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if not db_task:
            raise ValueError("任务不存在")

        config = db_task.config or {}

        source_ds = self.db.query(DataSource).filter(DataSource.id == config["source_id"]).first()
        target_ds = self.db.query(DataSource).filter(DataSource.id == config["target_id"]).first()
        if not source_ds or not target_ds:
            raise ValueError("任务关联的数据源不存在")

        db_query_timeout = int(runtime_settings.get("db_query_timeout", 60))
        source_timeout = db_query_timeout or source_ds.timeout
        target_timeout = db_query_timeout or target_ds.timeout

        source_conn = ConnectorFactory.create(
            db_type=source_ds.db_type,
            host=source_ds.host,
            port=source_ds.port,
            database=source_ds.database,
            username=source_ds.username,
            password=decrypt(source_ds.password_encrypted),
            schema=source_ds.schema,
            charset=source_ds.charset,
            timeout=source_timeout,
        )
        target_conn = ConnectorFactory.create(
            db_type=target_ds.db_type,
            host=target_ds.host,
            port=target_ds.port,
            database=target_ds.database,
            username=target_ds.username,
            password=decrypt(target_ds.password_encrypted),
            schema=target_ds.schema,
            charset=target_ds.charset,
            timeout=target_timeout,
        )

        source_conn.connect()
        target_conn.connect()

        completed_source_tables = self._extract_completed_source_tables(db_task.progress)

        try:
            compare_plan = self._build_compare_plan(source_conn, target_conn, config)
            self._update_task_progress(task_id, total_tables=len(compare_plan))

            logger.info(f"开始比对 {len(compare_plan)} 张表")

            all_structure_diffs: List[ComparatorStructureDiff] = []
            all_data_diffs: List[ComparatorDataDiff] = []
            structure_diff_tables: set[str] = set()
            data_diff_tables: set[str] = set()

            options = config.get("options", {}) or {}
            structure_options = options.get("structure_options", {}) or {}
            data_options = options.get("data_options", {}) or {}
            max_diffs = int(runtime_settings.get("max_diff_display", 1000))
            ignore_rules = self._load_effective_ignore_rules(options)

            structure_comparator = StructureComparator(source_conn, target_conn, structure_options)

            table_selection = config.get("table_selection", {}) or {}
            mode = table_selection.get("mode", "all")

            # 表存在性差异：mapping 模式只做映射表存在校验，不产出全库 extra
            missing_target_tables: set[str] = set()
            summary_tables: set[str] = {p["display_table"] for p in compare_plan}
            if mode != "mapping":
                source_tables_in_plan = [p["source_table"] for p in compare_plan]
                target_tables_all = [t.name for t in target_conn.get_tables()]
                existence_diffs = structure_comparator.compare_tables(source_tables_in_plan, target_tables_all)
                existence_diffs = self._apply_ignore_rules_to_structure_diffs(
                    diffs=existence_diffs,
                    rules=ignore_rules,
                    source_columns_map={},
                    target_columns_map={},
                    column_mapping={},
                )
                for diff in existence_diffs:
                    all_structure_diffs.append(diff)
                    structure_diff_tables.add(diff.table_name)
                    summary_tables.add(diff.table_name)
                    if diff.diff_type.value == "table_missing_in_target":
                        missing_target_tables.add(diff.table_name)

            for i, plan in enumerate(compare_plan):
                source_table = plan["source_table"]
                target_table = plan["target_table"]
                display_table = plan["display_table"]
                column_mapping = plan["column_mapping"]
                table_started_at = datetime.utcnow()
                table_structure_diffs_count = 0
                table_data_diffs_count = 0

                source_where_clause, target_where_clause = self._build_incremental_where_clauses(
                    options,
                    source_table=source_table,
                    target_table=target_table,
                    column_mapping=column_mapping,
                )
                source_row_count = 0
                target_row_count = 0
                try:
                    source_row_count = int(source_conn.get_row_count(source_table, source_where_clause))
                except Exception as exc:
                    logger.debug(f"获取源表 {source_table} 行数失败: {exc}")

                if self.task_manager.is_cancelled(task_id):
                    db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
                    if db_task:
                        db_task.status = "cancelled"
                        db_task.completed_at = datetime.utcnow()
                        self._persist_progress_snapshot(task_id, completed_source_tables)
                        self.db.commit()
                    self.task_manager.update_status(task_id, TaskStatus.CANCELLED)
                    self._run_auto_cleanup_if_enabled()
                    return

                await self.task_manager.wait_if_paused(task_id)

                self._update_task_progress(
                    task_id,
                    current_table=display_table,
                    completed_tables=i,
                )

                logger.debug(f"比对表: {display_table}")

                # 全库/指定/排除模式下，目标表不存在时跳过后续单表比对
                if mode != "mapping" and source_table in missing_target_tables:
                    self._upsert_table_stat(
                        task_id=task_id,
                        display_table=display_table,
                        source_table=source_table,
                        target_table=target_table,
                        source_row_count=source_row_count,
                        target_row_count=target_row_count,
                        compare_time_ms=int((datetime.utcnow() - table_started_at).total_seconds() * 1000),
                        structure_diffs_count=1,
                        data_diffs_count=0,
                    )
                    completed_source_tables.append(source_table)
                    self._persist_progress_snapshot(task_id, completed_source_tables)
                    self._update_task_progress(task_id, completed_tables=i + 1)
                    continue

                try:
                    target_row_count = int(target_conn.get_row_count(target_table, target_where_clause or source_where_clause))
                except Exception as exc:
                    logger.debug(f"获取目标表 {target_table} 行数失败: {exc}")

                source_columns = source_conn.get_columns(source_table)
                target_columns = target_conn.get_columns(target_table)
                source_columns_map = {c.name.lower(): c for c in source_columns}
                target_columns_map = {c.name.lower(): c for c in target_columns}

                # 结构比对
                self._update_task_progress(task_id, current_phase="structure")
                try:
                    structure_diffs = structure_comparator.compare_table_structure(
                        source_table,
                        {source_table: target_table},
                        column_mapping=column_mapping,
                    )
                    for diff in structure_diffs:
                        diff.table_name = display_table
                    structure_diffs = self._apply_ignore_rules_to_structure_diffs(
                        diffs=structure_diffs,
                        rules=ignore_rules,
                        source_columns_map=source_columns_map,
                        target_columns_map=target_columns_map,
                        column_mapping=column_mapping,
                    )
                    all_structure_diffs.extend(structure_diffs)
                    table_structure_diffs_count += len(structure_diffs)
                    if structure_diffs:
                        structure_diff_tables.add(display_table)
                except Exception as e:
                    logger.warning(f"表 {display_table} 结构比对失败: {e}")

                # 数据比对
                self._update_task_progress(task_id, current_phase="data")
                try:
                    primary_keys, pk_mapping, pk_error = self._resolve_primary_keys(
                        source_conn=source_conn,
                        options=options,
                        source_table=source_table,
                        target_table=target_table,
                    )

                    if not primary_keys:
                        data_diff = ComparatorDataDiff(
                            table_name=display_table,
                            primary_key={},
                            diff_type=DataDiffType.PRIMARY_KEY_MISSING,
                            diff_columns=[],
                            source_values={
                                "reason": pk_error or "未识别到主键，已跳过数据比对",
                                "source_table": source_table,
                            },
                            target_values={"target_table": target_table},
                        )
                        filtered_data_diffs = self._apply_ignore_rules_to_data_diffs(
                            diffs=[data_diff],
                            rules=ignore_rules,
                            source_columns_map=source_columns_map,
                        )
                        all_data_diffs.extend(filtered_data_diffs)
                        table_data_diffs_count += len(filtered_data_diffs)
                        if filtered_data_diffs:
                            data_diff_tables.add(display_table)
                    else:
                        effective_mapping = dict(column_mapping)
                        effective_mapping.update(pk_mapping)

                        data_comparator = DataComparator(source_conn, target_conn, data_options)
                        data_diffs = data_comparator.compare_data(
                            source_table,
                            primary_keys,
                            target_table=target_table,
                            column_mapping=effective_mapping,
                            where_clause=source_where_clause,
                            target_where_clause=target_where_clause,
                            max_diffs=max_diffs,
                        )
                        for diff in data_diffs:
                            diff.table_name = display_table
                        data_diffs = self._apply_ignore_rules_to_data_diffs(
                            diffs=data_diffs,
                            rules=ignore_rules,
                            source_columns_map=source_columns_map,
                        )
                        all_data_diffs.extend(data_diffs)
                        table_data_diffs_count += len(data_diffs)
                        if data_diffs:
                            data_diff_tables.add(display_table)
                except Exception as e:
                    logger.warning(f"表 {display_table} 数据比对失败: {e}")
                    data_diff = ComparatorDataDiff(
                        table_name=display_table,
                        primary_key={},
                        diff_type=DataDiffType.TABLE_COMPARE_ERROR,
                        diff_columns=[],
                        source_values={"error": str(e)},
                        target_values={"target_table": target_table},
                    )
                    filtered_data_diffs = self._apply_ignore_rules_to_data_diffs(
                        diffs=[data_diff],
                        rules=ignore_rules,
                        source_columns_map=source_columns_map,
                    )
                    all_data_diffs.extend(filtered_data_diffs)
                    table_data_diffs_count += len(filtered_data_diffs)
                    if filtered_data_diffs:
                        data_diff_tables.add(display_table)

                self._upsert_table_stat(
                    task_id=task_id,
                    display_table=display_table,
                    source_table=source_table,
                    target_table=target_table,
                    source_row_count=source_row_count,
                    target_row_count=target_row_count,
                    compare_time_ms=int((datetime.utcnow() - table_started_at).total_seconds() * 1000),
                    structure_diffs_count=table_structure_diffs_count,
                    data_diffs_count=table_data_diffs_count,
                )
                completed_source_tables.append(source_table)
                self._persist_progress_snapshot(task_id, completed_source_tables)
                self._update_task_progress(task_id, completed_tables=i + 1)

            result_id = await self._save_result(
                task_id,
                list(summary_tables),
                all_structure_diffs,
                all_data_diffs,
                structure_diff_tables,
                data_diff_tables,
            )

            db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
            if db_task:
                db_task.status = "completed"
                db_task.completed_at = datetime.utcnow()
                self._persist_progress_snapshot(task_id, completed_source_tables)
                self.db.commit()

            self.task_manager.set_result_id(task_id, result_id)
            self.task_manager.update_status(task_id, TaskStatus.COMPLETED)
            self._persist_progress_snapshot(task_id, completed_source_tables)

            logger.info(f"任务 {task_id} 完成，结果ID: {result_id}")
            self._run_auto_cleanup_if_enabled()

        finally:
            source_conn.disconnect()
            target_conn.disconnect()

    def _build_compare_plan(self, source_conn, target_conn, config: Dict) -> List[Dict[str, Any]]:
        """构建比对计划，统一为 source->target 表对"""
        source_tables = [t.name for t in source_conn.get_tables()]
        target_tables = [t.name for t in target_conn.get_tables()]
        source_set = set(source_tables)
        target_set = set(target_tables)

        table_selection = config.get("table_selection", {}) or {}
        options = config.get("options", {}) or {}
        mode = table_selection.get("mode", "all")

        compare_plan: List[Dict[str, Any]]
        if mode == "mapping":
            raw_mappings = options.get("table_mappings") or []
            if not raw_mappings:
                raise ValueError("映射比对模式下必须配置至少一组表映射")

            compare_plan = []
            seen_source_tables = set()
            for idx, item in enumerate(raw_mappings, start=1):
                source_table = (item or {}).get("source_table")
                target_table = (item or {}).get("target_table")
                if not source_table or not target_table:
                    raise ValueError(f"第 {idx} 组映射缺少源表或目标表")
                if source_table in seen_source_tables:
                    raise ValueError(f"源表 {source_table} 存在重复映射")

                seen_source_tables.add(source_table)
                if source_table not in source_set:
                    raise ValueError(f"源库不存在映射表: {source_table}")
                if target_table not in target_set:
                    raise ValueError(f"目标库不存在映射表: {target_table}")

                column_mapping = self._build_column_mapping(
                    item.get("column_mappings") or [],
                    source_table=source_table,
                    target_table=target_table,
                )
                display_table = source_table if source_table == target_table else f"{source_table} -> {target_table}"
                compare_plan.append(
                    {
                        "source_table": source_table,
                        "target_table": target_table,
                        "display_table": display_table,
                        "column_mapping": column_mapping,
                    }
                )
        else:
            compare_tables = self._get_compare_tables(source_tables, table_selection)
            compare_plan = [
                {
                    "source_table": table,
                    "target_table": table,
                    "display_table": table,
                    "column_mapping": {},
                }
                for table in compare_tables
            ]

        completed_for_resume = set((config.get("_resume") or {}).get("completed_source_tables") or [])
        if completed_for_resume:
            original_count = len(compare_plan)
            compare_plan = [item for item in compare_plan if item["source_table"] not in completed_for_resume]
            skipped_count = original_count - len(compare_plan)
            if skipped_count > 0:
                logger.info(f"命中断点续比，跳过已完成表 {skipped_count} 张")

        return compare_plan

    def _get_compare_tables(self, all_source_tables: List[str], table_selection: Dict[str, Any]) -> List[str]:
        """获取需要比对的表（同名模式）"""
        mode = table_selection.get("mode", "all")
        tables_list = table_selection.get("tables", []) or []

        if mode == "all":
            return all_source_tables
        if mode == "include":
            return [t for t in tables_list if t in all_source_tables]
        if mode == "exclude":
            return [t for t in all_source_tables if t not in tables_list]
        raise ValueError(f"不支持的表选择模式: {mode}")

    def _build_column_mapping(self, column_mappings: List[Dict[str, Any]], source_table: str, target_table: str) -> Dict[str, str]:
        """构建字段映射字典"""
        mapping = {}
        for idx, item in enumerate(column_mappings, start=1):
            source_column = (item or {}).get("source_column")
            target_column = (item or {}).get("target_column")
            if not source_column or not target_column:
                raise ValueError(f"表映射 {source_table} -> {target_table} 的第 {idx} 组字段映射不完整")
            if source_column in mapping:
                raise ValueError(f"表映射 {source_table} -> {target_table} 中字段 {source_column} 重复映射")
            mapping[source_column] = target_column
        return mapping

    def _validate_incremental_config(self, config: Dict[str, Any]) -> None:
        """校验增量配置"""
        options = (config or {}).get("options", {}) or {}
        mode = options.get("mode", "full")
        if mode != "incremental":
            return

        incremental_config = options.get("incremental_config") or {}
        if not incremental_config:
            raise ValueError("增量比对模式下必须配置 incremental_config")

        has_time_filter = bool(incremental_config.get("time_column"))
        has_batch_filter = bool(incremental_config.get("batch_column")) and incremental_config.get("batch_value") is not None

        if not has_time_filter and not has_batch_filter:
            raise ValueError("增量比对至少需要配置时间字段或批次字段")

    def _build_incremental_where_clauses(
        self,
        options: Dict[str, Any],
        source_table: str,
        target_table: str,
        column_mapping: Dict[str, str],
    ) -> Tuple[Optional[str], Optional[str]]:
        """构建增量过滤条件（源库/目标库）"""
        compare_mode = (options or {}).get("mode", "full")
        if compare_mode != "incremental":
            return None, None

        incremental_config = (options or {}).get("incremental_config") or {}
        source_time_column = incremental_config.get("time_column")
        target_time_column = incremental_config.get("target_time_column")
        start_time = incremental_config.get("start_time")
        end_time = incremental_config.get("end_time")
        batch_column = incremental_config.get("batch_column")
        batch_value = incremental_config.get("batch_value")
        target_batch_column = incremental_config.get("target_batch_column")

        source_conditions = []
        target_conditions = []

        if source_time_column:
            mapped_target_time = target_time_column or self._get_mapped_column_name(source_time_column, column_mapping)
            escaped_start = self._escape_sql_string(start_time) if start_time else None
            escaped_end = self._escape_sql_string(end_time) if end_time else None

            if escaped_start:
                source_conditions.append(f"{source_time_column} >= '{escaped_start}'")
                target_conditions.append(f"{mapped_target_time} >= '{escaped_start}'")
            if escaped_end:
                source_conditions.append(f"{source_time_column} <= '{escaped_end}'")
                target_conditions.append(f"{mapped_target_time} <= '{escaped_end}'")

        if batch_column and batch_value is not None:
            mapped_target_batch = target_batch_column or self._get_mapped_column_name(batch_column, column_mapping)
            batch_literal = f"'{self._escape_sql_string(str(batch_value))}'"
            source_conditions.append(f"{batch_column} = {batch_literal}")
            target_conditions.append(f"{mapped_target_batch} = {batch_literal}")

        source_where = " AND ".join(source_conditions) if source_conditions else None
        target_where = " AND ".join(target_conditions) if target_conditions else None

        if source_where:
            logger.debug(
                f"增量过滤生效: {source_table} -> {target_table}, "
                f"source_where={source_where}, target_where={target_where}"
            )
        return source_where, target_where

    def _resolve_primary_keys(
        self,
        source_conn,
        options: Dict[str, Any],
        source_table: str,
        target_table: str,
    ) -> Tuple[List[str], Dict[str, str], Optional[str]]:
        """解析主键，支持业务主键配置回退"""
        source_primary_keys = source_conn.get_primary_keys(source_table) or []
        if source_primary_keys:
            return source_primary_keys, {}, None

        raw_configs = (options or {}).get("table_primary_keys") or []
        matched = None
        for item in raw_configs:
            item_source_table = (item or {}).get("source_table")
            item_target_table = (item or {}).get("target_table")
            if not item_source_table:
                continue
            if item_source_table.lower() != source_table.lower():
                continue
            if item_target_table and item_target_table.lower() != target_table.lower():
                continue
            matched = item
            break

        if not matched:
            return [], {}, f"表 {source_table} 未识别到主键，且未配置业务主键"

        primary_keys = [pk for pk in (matched.get("primary_keys") or []) if str(pk).strip()]
        if not primary_keys:
            return [], {}, f"表 {source_table} 业务主键配置为空"

        primary_key_mapping = {}
        target_primary_keys = [pk for pk in (matched.get("target_primary_keys") or []) if str(pk).strip()]
        if target_primary_keys:
            if len(target_primary_keys) != len(primary_keys):
                return [], {}, f"表 {source_table} 业务主键配置不合法: primary_keys 与 target_primary_keys 数量不一致"
            for source_pk, target_pk in zip(primary_keys, target_primary_keys):
                primary_key_mapping[source_pk] = target_pk

        return primary_keys, primary_key_mapping, None

    def _get_mapped_column_name(self, source_column: str, column_mapping: Dict[str, str]) -> str:
        """按字段映射获取目标字段名（大小写不敏感）"""
        if source_column in column_mapping:
            return column_mapping[source_column]
        source_key = source_column.lower()
        for src, tgt in (column_mapping or {}).items():
            if str(src).lower() == source_key:
                return tgt
        return source_column

    def _escape_sql_string(self, value: str) -> str:
        """转义SQL字符串字面量"""
        return str(value).replace("'", "''")

    def _validate_mapping_task_config(self, source_ds: DataSource, target_ds: DataSource, config: Dict[str, Any]) -> None:
        """验证映射模式配置（含源/目标表存在性）"""
        try:
            source_conn = ConnectorFactory.create(
                db_type=source_ds.db_type,
                host=source_ds.host,
                port=source_ds.port,
                database=source_ds.database,
                username=source_ds.username,
                password=decrypt(source_ds.password_encrypted),
                schema=source_ds.schema,
                charset=source_ds.charset,
                timeout=source_ds.timeout,
            )
            target_conn = ConnectorFactory.create(
                db_type=target_ds.db_type,
                host=target_ds.host,
                port=target_ds.port,
                database=target_ds.database,
                username=target_ds.username,
                password=decrypt(target_ds.password_encrypted),
                schema=target_ds.schema,
                charset=target_ds.charset,
                timeout=target_ds.timeout,
            )

            source_conn.connect()
            target_conn.connect()
            try:
                self._build_compare_plan(source_conn, target_conn, config)
            finally:
                source_conn.disconnect()
                target_conn.disconnect()
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"映射配置校验失败: {e}")

    async def _save_result(
        self,
        task_id: str,
        tables: List[str],
        structure_diffs: List[ComparatorStructureDiff],
        data_diffs: List[ComparatorDataDiff],
        structure_diff_tables: set,
        data_diff_tables: set,
    ) -> str:
        """保存比对结果"""
        result_id = str(uuid.uuid4())

        table_set = set(tables)
        no_diff_tables = len(table_set - structure_diff_tables - data_diff_tables)

        structure_type_counts: Dict[str, int] = {}
        for diff in structure_diffs:
            structure_type_counts[diff.diff_type.value] = structure_type_counts.get(diff.diff_type.value, 0) + 1

        data_type_counts: Dict[str, int] = {}
        for diff in data_diffs:
            data_type_counts[diff.diff_type.value] = data_type_counts.get(diff.diff_type.value, 0) + 1

        summary = {
            "total_tables": len(table_set),
            "structure_match_tables": len(table_set - structure_diff_tables),
            "structure_diff_tables": len(structure_diff_tables),
            "data_match_tables": len(table_set - data_diff_tables),
            "data_diff_tables": len(data_diff_tables),
            "no_diff_tables": no_diff_tables,
            "total_structure_diffs": len(structure_diffs),
            "total_data_diffs": len(data_diffs),
            "structure_diff_type_counts": structure_type_counts,
            "data_diff_type_counts": data_type_counts,
        }

        result = CompareResult(id=result_id, task_id=task_id, summary=summary)
        self.db.add(result)

        for diff in structure_diffs:
            sd = StructureDiff(
                id=str(uuid.uuid4()),
                result_id=result_id,
                table_name=diff.table_name,
                diff_type=diff.diff_type.value,
                field_name=diff.field_name,
                source_value=diff.source_value,
                target_value=diff.target_value,
                diff_detail=diff.diff_detail,
            )
            self.db.add(sd)

        for diff in data_diffs:
            dd = DataDiffModel(
                id=str(uuid.uuid4()),
                result_id=result_id,
                table_name=diff.table_name,
                primary_key=diff.primary_key,
                diff_type=diff.diff_type.value,
                diff_columns=diff.diff_columns,
                source_values=diff.source_values,
                target_values=diff.target_values,
            )
            self.db.add(dd)

        self.db.commit()

        return result_id

    def get_task_progress(self, task_id: str) -> Optional[TaskStatusResponse]:
        """获取任务进度"""
        mem_task = self.task_manager.get_task(task_id)
        if mem_task:
            return TaskStatusResponse(
                task_id=task_id,
                status=mem_task.status.value,
                progress=TaskProgress(**mem_task.progress.to_dict()),
                error_message=mem_task.error_message,
                result_id=mem_task.result_id,
            )

        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if db_task:
            result = self.db.query(CompareResult).filter(CompareResult.task_id == task_id).first()
            return TaskStatusResponse(
                task_id=task_id,
                status=db_task.status,
                progress=TaskProgress(**(db_task.progress or {})),
                error_message=db_task.error_message,
                result_id=result.id if result else None,
            )

        return None

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if not db_task or db_task.status != "running":
            return False
        self.task_manager.ensure_task(task_id)
        result = self.task_manager.pause_task(task_id)
        if result:
            db_task.status = "paused"
            self._persist_progress_snapshot(task_id, self._extract_completed_source_tables(db_task.progress))
            self.db.commit()
        return result

    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if not db_task or db_task.status != "paused":
            return False
        self.task_manager.ensure_task(task_id)
        result = self.task_manager.resume_task(task_id)
        if result:
            db_task.status = "running"
            self.db.commit()
        return result

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if not db_task:
            return False
        if db_task.status in {"completed", "failed", "cancelled"}:
            return False

        self.task_manager.ensure_task(task_id)
        result = self.task_manager.cancel_task(task_id)
        if result:
            db_task.status = "cancelled"
            db_task.completed_at = datetime.utcnow()
            self._persist_progress_snapshot(task_id, self._extract_completed_source_tables(db_task.progress))
            self.db.commit()
            self._run_auto_cleanup_if_enabled()
        return result

    def _load_effective_ignore_rules(self, options: Dict[str, Any]) -> List[IgnoreRule]:
        """加载生效忽略规则：显式配置优先，否则使用全局启用规则。"""
        explicit_ids = (options or {}).get("ignore_rules") or []
        if explicit_ids:
            records = self.db.query(IgnoreRule).filter(IgnoreRule.id.in_(explicit_ids)).all()
            mapping = {r.id: r for r in records}
            return [mapping[rid] for rid in explicit_ids if rid in mapping]

        return self.db.query(IgnoreRule).filter(IgnoreRule.enabled.is_(True)).order_by(IgnoreRule.created_at.asc()).all()

    def _apply_ignore_rules_to_structure_diffs(
        self,
        diffs: List[ComparatorStructureDiff],
        rules: List[IgnoreRule],
        source_columns_map: Dict[str, Any],
        target_columns_map: Dict[str, Any],
        column_mapping: Dict[str, str],
    ) -> List[ComparatorStructureDiff]:
        if not rules:
            return diffs

        filtered: List[ComparatorStructureDiff] = []
        for diff in diffs:
            if self._should_ignore_structure_diff(
                diff=diff,
                rules=rules,
                source_columns_map=source_columns_map,
                target_columns_map=target_columns_map,
                column_mapping=column_mapping,
            ):
                continue
            filtered.append(diff)
        return filtered

    def _apply_ignore_rules_to_data_diffs(
        self,
        diffs: List[ComparatorDataDiff],
        rules: List[IgnoreRule],
        source_columns_map: Dict[str, Any],
    ) -> List[ComparatorDataDiff]:
        if not rules:
            return diffs

        filtered: List[ComparatorDataDiff] = []
        for diff in diffs:
            if self._should_ignore_by_rule_type("table", diff.table_name, rules, table_name=diff.table_name):
                continue
            if self._should_ignore_by_rule_type("diffType", diff.diff_type.value, rules, table_name=diff.table_name):
                continue

            if diff.diff_columns:
                kept_cols: List[str] = []
                for col in diff.diff_columns:
                    if self._should_ignore_by_rule_type("column", col, rules, table_name=diff.table_name):
                        continue
                    source_col = source_columns_map.get(col.lower())
                    source_type = source_col.data_type if source_col else ""
                    if source_type and self._should_ignore_by_rule_type("dataType", source_type, rules, table_name=diff.table_name):
                        continue
                    kept_cols.append(col)

                if not kept_cols:
                    continue

                if len(kept_cols) != len(diff.diff_columns):
                    source_values = diff.source_values or {}
                    target_values = diff.target_values or {}
                    diff = ComparatorDataDiff(
                        table_name=diff.table_name,
                        primary_key=diff.primary_key,
                        diff_type=diff.diff_type,
                        diff_columns=kept_cols,
                        source_values={k: source_values.get(k) for k in kept_cols if k in source_values},
                        target_values={k: target_values.get(k) for k in kept_cols if k in target_values},
                    )

            filtered.append(diff)

        return filtered

    def _should_ignore_structure_diff(
        self,
        diff: ComparatorStructureDiff,
        rules: List[IgnoreRule],
        source_columns_map: Dict[str, Any],
        target_columns_map: Dict[str, Any],
        column_mapping: Dict[str, str],
    ) -> bool:
        if self._should_ignore_by_rule_type("table", diff.table_name, rules, table_name=diff.table_name):
            return True
        if self._should_ignore_by_rule_type("diffType", diff.diff_type.value, rules, table_name=diff.table_name):
            return True

        if diff.field_name:
            if self._should_ignore_by_rule_type("column", diff.field_name, rules, table_name=diff.table_name):
                return True

            source_col = source_columns_map.get(diff.field_name.lower())
            target_col_name = self._get_mapped_column_name(diff.field_name, column_mapping)
            target_col = target_columns_map.get(str(target_col_name).lower())
            source_type = source_col.data_type if source_col else ""
            target_type = target_col.data_type if target_col else ""

            if source_type and self._should_ignore_by_rule_type("dataType", source_type, rules, table_name=diff.table_name):
                return True
            if target_type and self._should_ignore_by_rule_type("dataType", target_type, rules, table_name=diff.table_name):
                return True

        return False

    def _should_ignore_by_rule_type(self, rule_type: str, value: str, rules: List[IgnoreRule], table_name: str) -> bool:
        candidate = str(value or "")
        for rule in rules:
            if rule.rule_type != rule_type:
                continue
            if not self._rule_applies_to_table(rule, table_name):
                continue
            if self._match_pattern(candidate, rule.pattern):
                return True
        return False

    def _rule_applies_to_table(self, rule: IgnoreRule, table_name: str) -> bool:
        if not rule.tables:
            return True
        table_value = str(table_name or "").lower()
        for item in rule.tables:
            if self._match_pattern(table_value, str(item)):
                return True
        return False

    def _match_pattern(self, value: str, pattern: str) -> bool:
        value_norm = str(value or "").lower()
        pattern_norm = str(pattern or "").lower().replace("%", "*").replace("_", "?")
        if not pattern_norm:
            return False
        if "*" not in pattern_norm and "?" not in pattern_norm:
            return value_norm == pattern_norm
        return fnmatch.fnmatch(value_norm, pattern_norm)

    def _get_runtime_settings(self) -> Dict[str, Any]:
        defaults: Dict[str, Any] = {
            "compare_thread_count": 4,
            "db_query_timeout": 60,
            "compare_timeout": 3600,
            "history_retention_days": 90,
            "history_max_count": 500,
            "default_page_size": 10000,
            "max_diff_display": 1000,
            "auto_cleanup_enabled": True,
        }

        rows = self.db.query(SystemSetting).all()
        for row in rows:
            try:
                defaults[row.key] = json.loads(row.value)
            except Exception:
                defaults[row.key] = row.value

        return defaults

    def _update_task_progress(self, task_id: str, **kwargs) -> None:
        self.task_manager.update_progress(task_id, **kwargs)
        self._persist_progress_snapshot(task_id)

    def _persist_progress_snapshot(self, task_id: str, completed_source_tables: Optional[List[str]] = None) -> None:
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        mem_task = self.task_manager.get_task(task_id)
        if not db_task or not mem_task:
            return

        payload = mem_task.progress.to_dict()
        existing_progress = db_task.progress if isinstance(db_task.progress, dict) else {}
        if completed_source_tables is not None:
            payload["completed_source_tables"] = completed_source_tables
        elif existing_progress.get("completed_source_tables"):
            payload["completed_source_tables"] = existing_progress.get("completed_source_tables")
        if existing_progress.get("table_stats"):
            payload["table_stats"] = existing_progress.get("table_stats")

        db_task.progress = payload
        self.db.commit()

    def _upsert_table_stat(
        self,
        task_id: str,
        display_table: str,
        source_table: str,
        target_table: str,
        source_row_count: int,
        target_row_count: int,
        compare_time_ms: int,
        structure_diffs_count: int,
        data_diffs_count: int,
    ) -> None:
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if not db_task:
            return
        progress = db_task.progress if isinstance(db_task.progress, dict) else {}
        table_stats = progress.get("table_stats", {}) if isinstance(progress.get("table_stats"), dict) else {}
        table_stats[display_table] = {
            "source_table": source_table,
            "target_table": target_table,
            "source_row_count": int(source_row_count or 0),
            "target_row_count": int(target_row_count or 0),
            "compare_time_ms": int(compare_time_ms or 0),
            "structure_diffs_count": int(structure_diffs_count or 0),
            "data_diffs_count": int(data_diffs_count or 0),
        }
        progress["table_stats"] = table_stats
        db_task.progress = progress
        self.db.commit()

    def _extract_completed_source_tables(self, progress: Optional[Dict[str, Any]]) -> List[str]:
        if not progress:
            return []
        raw = progress.get("completed_source_tables") if isinstance(progress, dict) else None
        if not raw:
            return []
        return [str(item) for item in raw if str(item).strip()]

    def _mark_task_failed(self, task_id: str, error_message: str) -> None:
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if db_task:
            db_task.status = "failed"
            db_task.error_message = error_message
            db_task.completed_at = datetime.utcnow()
            self._persist_progress_snapshot(task_id, self._extract_completed_source_tables(db_task.progress))
            self.db.commit()
        self.task_manager.update_status(task_id, TaskStatus.FAILED, error_message)
        self._run_auto_cleanup_if_enabled()

    def _compute_config_hash(self, config: Dict[str, Any]) -> str:
        config_clone = json.loads(json.dumps(config, ensure_ascii=False))
        config_clone.pop("_meta", None)
        config_clone.pop("_resume", None)
        raw = json.dumps(config_clone, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _prepare_resume_from_checkpoint(self, source_id: str, target_id: str, config_hash: str) -> Optional[Dict[str, Any]]:
        deadline = datetime.utcnow() - timedelta(days=7)
        candidates = (
            self.db.query(CompareTask)
            .filter(CompareTask.source_id == source_id)
            .filter(CompareTask.target_id == target_id)
            .filter(CompareTask.created_at >= deadline)
            .filter(CompareTask.status.in_(["failed", "cancelled"]))
            .order_by(CompareTask.created_at.desc())
            .all()
        )

        for task in candidates:
            task_config = task.config or {}
            task_hash = (task_config.get("_meta") or {}).get("config_hash")
            if task_hash != config_hash:
                continue
            completed = self._extract_completed_source_tables(task.progress)
            if not completed:
                continue
            return {
                "from_task_id": task.id,
                "completed_source_tables": completed,
                "valid_until": (task.created_at + timedelta(days=7)).isoformat() if task.created_at else None,
            }

        return None

    def _run_auto_cleanup_if_enabled(self) -> None:
        try:
            HistoryService(self.db).auto_cleanup_by_settings()
        except Exception as exc:
            logger.warning(f"自动清理历史记录失败: {exc}")
