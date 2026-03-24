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
from app.core.comparator.structure import StructureComparator, StructureDiffType
from app.core.comparator.data import DataComparator, DataDiffType
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
        
        # 创建任务记录
        task = CompareTask(
            id=str(uuid.uuid4()),
            source_id=request.source_id,
            target_id=request.target_id,
            status="pending",
            config=request.model_dump()
        )
        
        self.db.add(task)
        self.db.commit()
        
        # 创建内存任务
        mem_task = self.task_manager.create_task()
        mem_task.id = task.id  # 使用数据库任务ID
        
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
                # 获取比对表列表
                tables = self._get_compare_tables(source_conn, config)
                self.task_manager.update_progress(task_id, total_tables=len(tables))
                
                logger.info(f"开始比对 {len(tables)} 张表")
                
                all_structure_diffs = []
                all_data_diffs = []
                structure_diff_tables = set()
                data_diff_tables = set()
                
                # 获取比对选项
                options = config.get('options', {})
                structure_options = options.get('structure_options', {})
                data_options = options.get('data_options', {})
                
                # 逐表比对
                for i, table in enumerate(tables):
                    # 检查是否取消
                    if self.task_manager.is_cancelled(task_id):
                        raise Exception("任务已取消")
                    
                    # 等待暂停
                    await self.task_manager.wait_if_paused(task_id)
                    
                    self.task_manager.update_progress(
                        task_id, 
                        current_table=table,
                        completed_tables=i
                    )
                    
                    logger.debug(f"比对表: {table}")
                    
                    # 结构比对
                    self.task_manager.update_progress(task_id, current_phase='structure')
                    structure_comparator = StructureComparator(
                        source_conn, target_conn, structure_options
                    )
                    
                    try:
                        structure_diffs = structure_comparator.compare_table_structure(table)
                        all_structure_diffs.extend(structure_diffs)
                        if structure_diffs:
                            structure_diff_tables.add(table)
                    except Exception as e:
                        logger.warning(f"表 {table} 结构比对失败: {e}")
                    
                    # 数据比对
                    self.task_manager.update_progress(task_id, current_phase='data')
                    try:
                        primary_keys = source_conn.get_primary_keys(table)
                        if primary_keys:
                            data_comparator = DataComparator(
                                source_conn, target_conn, data_options
                            )
                            data_diffs = data_comparator.compare_data(table, primary_keys)
                            all_data_diffs.extend(data_diffs)
                            if data_diffs:
                                data_diff_tables.add(table)
                    except Exception as e:
                        logger.warning(f"表 {table} 数据比对失败: {e}")
                    
                    self.task_manager.update_progress(task_id, completed_tables=i + 1)
                
                # 保存结果
                result_id = await self._save_result(
                    task_id, tables, all_structure_diffs, all_data_diffs,
                    structure_diff_tables, data_diff_tables
                )
                
                # 更新任务状态
                db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
                db_task.status = "completed"
                db_task.completed_at = datetime.utcnow()
                self.db.commit()
                
                self.task_manager.update_status(task_id, TaskStatus.COMPLETED)
                self.task_manager.set_result_id(task_id, result_id)
                
                logger.info(f"任务 {task_id} 完成，结果ID: {result_id}")
                
            finally:
                source_conn.disconnect()
                target_conn.disconnect()
                
        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {e}")
            
            # 更新数据库任务状态
            db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
            if db_task:
                db_task.status = "failed"
                db_task.error_message = str(e)
                db_task.completed_at = datetime.utcnow()
                self.db.commit()
            
            self.task_manager.update_status(task_id, TaskStatus.FAILED, str(e))
    
    def _get_compare_tables(self, conn, config: Dict) -> List[str]:
        """获取需要比对的表"""
        all_tables = [t.name for t in conn.get_tables()]
        table_selection = config.get('table_selection', {})
        mode = table_selection.get('mode', 'all')
        tables_list = table_selection.get('tables', [])
        
        if mode == 'all':
            return all_tables
        elif mode == 'include':
            return [t for t in tables_list if t in all_tables]
        else:  # exclude
            return [t for t in all_tables if t not in tables_list]
    
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
                error_message=mem_task.error_message
            )
        
        # 从数据库获取
        db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
        if db_task:
            return TaskStatusResponse(
                task_id=task_id,
                status=db_task.status,
                progress=TaskProgress(**(db_task.progress or {})),
                error_message=db_task.error_message
            )
        
        return None
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        result = self.task_manager.pause_task(task_id)
        if result:
            db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
            if db_task:
                db_task.status = "paused"
                self.db.commit()
        return result
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        result = self.task_manager.resume_task(task_id)
        if result:
            db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
            if db_task:
                db_task.status = "running"
                self.db.commit()
        return result
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        result = self.task_manager.cancel_task(task_id)
        if result:
            db_task = self.db.query(CompareTask).filter(CompareTask.id == task_id).first()
            if db_task:
                db_task.status = "cancelled"
                db_task.completed_at = datetime.utcnow()
                self.db.commit()
        return result
