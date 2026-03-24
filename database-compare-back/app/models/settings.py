"""设置相关模型"""
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean
from datetime import datetime
import uuid

from app.models.base import Base


class IgnoreRule(Base):
    """忽略规则表"""
    __tablename__ = "ignore_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    rule_type = Column(String(20), nullable=False)  # column/dataType/diffType/table
    pattern = Column(String(255), nullable=False)
    tables = Column(JSON, nullable=True)  # 适用的表列表
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompareTemplate(Base):
    """比对模板表"""
    __tablename__ = "compare_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)  # 模板配置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemSetting(Base):
    """系统设置表"""
    __tablename__ = "system_settings"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
