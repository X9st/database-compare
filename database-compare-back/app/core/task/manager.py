"""任务管理器"""
import asyncio
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """任务进度"""
    total_tables: int = 0
    completed_tables: int = 0
    current_table: str = ""
    current_phase: str = ""  # structure / data
    percentage: float = 0.0
    start_time: Optional[datetime] = None
    elapsed_seconds: int = 0
    estimated_remaining_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tables": self.total_tables,
            "completed_tables": self.completed_tables,
            "current_table": self.current_table,
            "current_phase": self.current_phase,
            "percentage": self.percentage,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining_seconds": self.estimated_remaining_seconds
        }


@dataclass
class CompareTask:
    """比对任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    progress: TaskProgress = field(default_factory=TaskProgress)
    error_message: Optional[str] = None
    result_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.id,
            "status": self.status.value,
            "progress": self.progress.to_dict(),
            "error_message": self.error_message,
            "result_id": self.result_id
        }


class TaskManager:
    """任务管理器（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tasks: Dict[str, CompareTask] = {}
            cls._instance._progress_callbacks: Dict[str, Callable] = {}
            cls._instance._cancel_events: Dict[str, asyncio.Event] = {}
            cls._instance._pause_events: Dict[str, asyncio.Event] = {}
        return cls._instance
    
    def create_task(self) -> CompareTask:
        """创建任务"""
        task = CompareTask()
        self._tasks[task.id] = task
        self._cancel_events[task.id] = asyncio.Event()
        self._pause_events[task.id] = asyncio.Event()
        self._pause_events[task.id].set()  # 初始不暂停
        return task
    
    def get_task(self, task_id: str) -> Optional[CompareTask]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def update_status(self, task_id: str, status: TaskStatus, 
                      error_message: str = None) -> None:
        """更新任务状态"""
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            task.error_message = error_message
            self._notify_progress(task_id)
    
    def update_progress(self, task_id: str, **kwargs) -> None:
        """更新任务进度"""
        task = self._tasks.get(task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task.progress, key):
                    setattr(task.progress, key, value)
            
            # 计算百分比
            if task.progress.total_tables > 0:
                task.progress.percentage = round(
                    task.progress.completed_tables / task.progress.total_tables * 100, 2
                )
            
            # 计算耗时
            if task.progress.start_time:
                task.progress.elapsed_seconds = int(
                    (datetime.utcnow() - task.progress.start_time).total_seconds()
                )
                
                # 估算剩余时间
                if task.progress.completed_tables > 0:
                    avg_time_per_table = task.progress.elapsed_seconds / task.progress.completed_tables
                    remaining_tables = task.progress.total_tables - task.progress.completed_tables
                    task.progress.estimated_remaining_seconds = int(avg_time_per_table * remaining_tables)
            
            self._notify_progress(task_id)
    
    def set_result_id(self, task_id: str, result_id: str) -> None:
        """设置结果ID"""
        task = self._tasks.get(task_id)
        if task:
            task.result_id = result_id
    
    def register_callback(self, task_id: str, callback: Callable) -> None:
        """注册进度回调"""
        self._progress_callbacks[task_id] = callback
    
    def unregister_callback(self, task_id: str) -> None:
        """取消注册进度回调"""
        if task_id in self._progress_callbacks:
            del self._progress_callbacks[task_id]
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self._cancel_events:
            self._cancel_events[task_id].set()
            return True
        return False
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        if task_id in self._pause_events:
            self._pause_events[task_id].clear()
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.PAUSED
                self._notify_progress(task_id)
            return True
        return False
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        if task_id in self._pause_events:
            self._pause_events[task_id].set()
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.RUNNING
                self._notify_progress(task_id)
            return True
        return False
    
    def is_cancelled(self, task_id: str) -> bool:
        """检查任务是否被取消"""
        event = self._cancel_events.get(task_id)
        return event.is_set() if event else False
    
    async def wait_if_paused(self, task_id: str) -> None:
        """如果暂停则等待"""
        event = self._pause_events.get(task_id)
        if event:
            await event.wait()
    
    def _notify_progress(self, task_id: str) -> None:
        """通知进度更新"""
        callback = self._progress_callbacks.get(task_id)
        if callback:
            task = self._tasks.get(task_id)
            if task:
                try:
                    callback(task)
                except Exception:
                    pass
    
    def cleanup_task(self, task_id: str) -> None:
        """清理任务资源"""
        if task_id in self._cancel_events:
            del self._cancel_events[task_id]
        if task_id in self._pause_events:
            del self._pause_events[task_id]
        if task_id in self._progress_callbacks:
            del self._progress_callbacks[task_id]
