"""比对服务"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import uuid
from sqlalchemy.orm import Session
from loguru import logger

from app.models.datasource import DataSource
from app.models.compare_task import CompareTask, CompareResult, StructureDiff, DataDiff
from app.schemas.compare import CreateTaskRequest, TaskProgress, TaskStatusResponse
from app.core.connector import ConnectorFactory
from app.core.comparator.structure import StructureComparator
from app.core.comparator.data import DataComparator
from app.core.task.manager import TaskManager, TaskStatus
from app.utils.crypto import decrypt


class CompareService:
    """比对服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.task_manager = TaskManager()
    
    def create_task(self, request: CreateTaskRequest) -> Dict[str, Any]:
        """创建比对任务"""
        # 验证数据源存在
        source_ds = self.db.query(DataSource).filter(
            DataSource.id == request.source_id
        ).first()
        target_ds = self.db.query(DataSource).filter(
            DataSource.id == request.target_id
        ).first()
        
        if not source_ds:
            raise ValueError(f"源数据源不存在: {request.source_id}")
        if not target_ds:
            raise ValueError(f"目标数据源不存在: {request.target_id}")

        config_data = request.model_dump()
        if config_data.get("table_selection", {}).get("mode") == "mapping":
            self._validate_mapping_task_config(source_ds, target_ds, config_data)
        
        # 创建任务记录
        task = CompareTask(
            id=str(uuid.uuid4()),
            source_id=request.source_id,
            target_id=request.target_id,
            status="pending",
            config=config_data
        )
        
        self.db.add(task)
        self.db.commit()
        
        # 创建内存任务，确保任务ID与数据库一致
        self.task_manager.create_task(task_id=task.id)
        
        return {
            "task_id": task.id,
            "status": "pending",
            "created_at": task.created_at
        }
    
    async def start_task(self, task_id: str) -> Dict[str, Any]:
        """启动比对任务"""
        # 获取任务
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if not db_task:
            raise ValueError("任务不存在")
        
        if db_task.status not in ["pending", "paused"]:
            raise ValueError(f"任务状态 {db_task.status} 不允许启动")

        self.task_manager.ensure_task(task_id)
        
        # 更新状态
        db_task.status = "running"
        db_task.started_at = datetime.utcnow()
        self.db.commit()
        
        # 异步执行比对
        asyncio.create_task(self._execute_compare(task_id))
        
        return {"task_id": task_id, "status": "running"}
    
    async def _execute_compare(self, task_id: str) -> None:
        """执行比对（异步）"""
        try:
            self.task_manager.ensure_task(task_id)
            self.task_manager.update_status(task_id, TaskStatus.RUNNING)
            self.task_manager.update_progress(task_id, start_time=datetime.utcnow())
            
            # 获取任务配置
            db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
            config = db_task.config
            
            # 获取数据源配置
            source_ds = self.db.query(DataSource).filter(
                DataSource.id == config['source_id']
            ).first()
            target_ds = self.db.query(DataSource).filter(
                DataSource.id == config['target_id']
            ).first()
            
            # 创建连接器
            source_conn = ConnectorFactory.create(
                db_type=source_ds.db_type,
                host=source_ds.host,
                port=source_ds.port,
                database=source_ds.database,
                username=source_ds.username,
                password=decrypt(source_ds.password_encrypted),
                schema=source_ds.schema,
                charset=source_ds.charset,
                timeout=source_ds.timeout
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
                timeout=target_ds.timeout
            )
            
            # 连接数据库
            source_conn.connect()
            target_conn.connect()
            
            try:
                # 构建比对计划
                compare_plan = self._build_compare_plan(source_conn, target_conn, config)
                self.task_manager.update_progress(task_id, total_tables=len(compare_plan))
                
                logger.info(f"开始比对 {len(compare_plan)} 张表")
                
                all_structure_diffs = []
                all_data_diffs = []
                structure_diff_tables = set()
                data_diff_tables = set()
                
                # 获取比对选项
                options = config.get('options', {})
                structure_options = options.get('structure_options', {})
                data_options = options.get('data_options', {})
                
                # 逐表比对
                for i, plan in enumerate(compare_plan):
                    source_table = plan["source_table"]
                    target_table = plan["target_table"]
                    display_table = plan["display_table"]
                    column_mapping = plan["column_mapping"]

                    # 检查是否取消
                    if self.task_manager.is_cancelled(task_id):
                        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
                        if db_task:
                            db_task.status = "cancelled"
                            db_task.completed_at = datetime.utcnow()
                            self.db.commit()
                        self.task_manager.update_status(task_id, TaskStatus.CANCELLED)
                        return
                    
                    # 等待暂停
                    await self.task_manager.wait_if_paused(task_id)
                    
                    self.task_manager.update_progress(
                        task_id, 
                        current_table=display_table,
                        completed_tables=i
                    )
                    
                    logger.debug(f"比对表: {display_table}")
                    
                    # 结构比对
                    self.task_manager.update_progress(task_id, current_phase='structure')
                    structure_comparator = StructureComparator(
                        source_conn, target_conn, structure_options
                    )
                    
                    try:
                        structure_diffs = structure_comparator.compare_table_structure(
                            source_table,
                            {source_table: target_table}
                        )
                        for diff in structure_diffs:
                            diff.table_name = display_table
                        all_structure_diffs.extend(structure_diffs)
                        if structure_diffs:
                            structure_diff_tables.add(display_table)
                    except Exception as e:
                        logger.warning(f"表 {display_table} 结构比对失败: {e}")
                    
                    # 数据比对
                    self.task_manager.update_progress(task_id, current_phase='data')
                    try:
                        primary_keys = source_conn.get_primary_keys(source_table)
                        if primary_keys:
                            data_comparator = DataComparator(
                                source_conn, target_conn, data_options
                            )
                            data_diffs = data_comparator.compare_data(
                                source_table,
                                primary_keys,
                                target_table=target_table,
                                column_mapping=column_mapping
                            )
                            for diff in data_diffs:
                                diff.table_name = display_table
                            all_data_diffs.extend(data_diffs)
                            if data_diffs:
                                data_diff_tables.add(display_table)
                    except Exception as e:
                        logger.warning(f"表 {display_table} 数据比对失败: {e}")
                    
                    self.task_manager.update_progress(task_id, completed_tables=i + 1)
                
                # 保存结果
                result_id = await self._save_result(
                    task_id, [p["display_table"] for p in compare_plan], all_structure_diffs, all_data_diffs,
                    structure_diff_tables, data_diff_tables
                )
                
                # 更新任务状态
                db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
                db_task.status = "completed"
                db_task.completed_at = datetime.utcnow()
                self.db.commit()
                
                self.task_manager.set_result_id(task_id, result_id)
                self.task_manager.update_status(task_id, TaskStatus.COMPLETED)
                
                logger.info(f"任务 {task_id} 完成，结果ID: {result_id}")
                
            finally:
                source_conn.disconnect()
                target_conn.disconnect()
                
        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {e}")
            
            # 更新数据库任务状态
            db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
            if db_task:
                error_message = str(e)
                if "取消" in error_message:
                    db_task.status = "cancelled"
                    self.task_manager.update_status(task_id, TaskStatus.CANCELLED, error_message)
                else:
                    db_task.status = "failed"
                    db_task.error_message = error_message
                    self.task_manager.update_status(task_id, TaskStatus.FAILED, error_message)
                db_task.completed_at = datetime.utcnow()
                self.db.commit()
    
    def _build_compare_plan(self, source_conn, target_conn, config: Dict) -> List[Dict[str, Any]]:
        """构建比对计划，统一为 source->target 表对"""
        source_tables = [t.name for t in source_conn.get_tables()]
        target_tables = [t.name for t in target_conn.get_tables()]
        source_set = set(source_tables)
        target_set = set(target_tables)

        table_selection = config.get("table_selection", {}) or {}
        options = config.get("options", {}) or {}
        mode = table_selection.get("mode", "all")

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
                    target_table=target_table
                )
                display_table = source_table if source_table == target_table else f"{source_table} -> {target_table}"
                compare_plan.append({
                    "source_table": source_table,
                    "target_table": target_table,
                    "display_table": display_table,
                    "column_mapping": column_mapping
                })

            return compare_plan

        compare_tables = self._get_compare_tables(source_tables, table_selection)
        return [{
            "source_table": table,
            "target_table": table,
            "display_table": table,
            "column_mapping": {}
        } for table in compare_tables]

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

    def _build_column_mapping(self, column_mappings: List[Dict[str, Any]],
                              source_table: str, target_table: str) -> Dict[str, str]:
        """构建字段映射字典"""
        mapping = {}
        for idx, item in enumerate(column_mappings, start=1):
            source_column = (item or {}).get("source_column")
            target_column = (item or {}).get("target_column")
            if not source_column or not target_column:
                raise ValueError(
                    f"表映射 {source_table} -> {target_table} 的第 {idx} 组字段映射不完整"
                )
            if source_column in mapping:
                raise ValueError(
                    f"表映射 {source_table} -> {target_table} 中字段 {source_column} 重复映射"
                )
            mapping[source_column] = target_column
        return mapping

    def _validate_mapping_task_config(self, source_ds: DataSource, target_ds: DataSource,
                                      config: Dict[str, Any]) -> None:
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
                timeout=source_ds.timeout
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
                timeout=target_ds.timeout
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
    
    async def _save_result(self, task_id: str, tables: List[str],
                           structure_diffs: list, data_diffs: list,
                           structure_diff_tables: set, data_diff_tables: set) -> str:
        """保存比对结果"""
        result_id = str(uuid.uuid4())
        
        # 创建结果汇总
        summary = {
            "total_tables": len(tables),
            "structure_match_tables": len(tables) - len(structure_diff_tables),
            "structure_diff_tables": len(structure_diff_tables),
            "data_match_tables": len(tables) - len(data_diff_tables),
            "data_diff_tables": len(data_diff_tables),
            "total_structure_diffs": len(structure_diffs),
            "total_data_diffs": len(data_diffs)
        }
        
        # 保存结果
        result = CompareResult(
            id=result_id,
            task_id=task_id,
            summary=summary
        )
        self.db.add(result)
        
        # 保存结构差异
        for diff in structure_diffs:
            sd = StructureDiff(
                id=str(uuid.uuid4()),
                result_id=result_id,
                table_name=diff.table_name,
                diff_type=diff.diff_type.value,
                field_name=diff.field_name,
                source_value=diff.source_value,
                target_value=diff.target_value,
                diff_detail=diff.diff_detail
            )
            self.db.add(sd)
        
        # 保存数据差异
        for diff in data_diffs:
            dd = DataDiff(
                id=str(uuid.uuid4()),
                result_id=result_id,
                table_name=diff.table_name,
                primary_key=diff.primary_key,
                diff_type=diff.diff_type.value,
                diff_columns=diff.diff_columns,
                source_values=diff.source_values,
                target_values=diff.target_values
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
                result_id=mem_task.result_id
            )
        
        # 从数据库获取
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if db_task:
            result = self.db.query(CompareResult).filter(
                CompareResult.task_id == task_id
            ).first()
            return TaskStatusResponse(
                task_id=task_id,
                status=db_task.status,
                progress=TaskProgress(**(db_task.progress or {})),
                error_message=db_task.error_message,
                result_id=result.id if result else None
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
            self.db.commit()
        return result
