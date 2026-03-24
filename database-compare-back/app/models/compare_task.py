"""比对任务和结果模型"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from datetime import datetime
import uuid

from app.models.base import Base


class CompareTask(Base):
    """比对任务表"""
    __tablename__ = "compare_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("datasources.id"), nullable=False)
    target_id = Column(String(36), ForeignKey("datasources.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending/running/paused/completed/failed/cancelled
    config = Column(JSON, nullable=False)  # 比对配置
    progress = Column(JSON, nullable=True)  # 进度信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompareResult(Base):
    """比对结果表"""
    __tablename__ = "compare_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("compare_tasks.id"), nullable=False)
    summary = Column(JSON, nullable=False)  # 汇总信息
    created_at = Column(DateTime, default=datetime.utcnow)


class StructureDiff(Base):
    """结构差异表"""
    __tablename__ = "structure_diffs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    result_id = Column(String(36), ForeignKey("compare_results.id"), nullable=False)
    table_name = Column(String(255), nullable=False)
    diff_type = Column(String(50), nullable=False)
    field_name = Column(String(255), nullable=True)
    source_value = Column(Text, nullable=True)
    target_value = Column(Text, nullable=True)
    diff_detail = Column(Text, nullable=True)


class DataDiff(Base):
    """数据差异表"""
    __tablename__ = "data_diffs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    result_id = Column(String(36), ForeignKey("compare_results.id"), nullable=False)
    table_name = Column(String(255), nullable=False)
    primary_key = Column(JSON, nullable=False)
    diff_type = Column(String(50), nullable=False)
    diff_columns = Column(JSON, nullable=True)
    source_values = Column(JSON, nullable=True)
    target_values = Column(JSON, nullable=True)
