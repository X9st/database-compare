"""数据源模型"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class DataSourceGroup(Base):
    """数据源分组表"""
    __tablename__ = "datasource_groups"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    datasources = relationship("DataSource", back_populates="group")


class DataSource(Base):
    """数据源表"""
    __tablename__ = "datasources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    group_id = Column(String(36), ForeignKey("datasource_groups.id"), nullable=True)
    db_type = Column(String(20), nullable=False)  # mysql/oracle/dm/inceptor/excel/dbf
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database = Column(String(100), nullable=False)
    schema = Column(String(100), nullable=True)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    extra_config = Column(JSON, nullable=True)  # 文件源配置（storage_key/file_type 等）
    charset = Column(String(20), default="UTF-8")
    timeout = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    group = relationship("DataSourceGroup", back_populates="datasources")
