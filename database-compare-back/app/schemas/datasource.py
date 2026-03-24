"""数据源相关Schema"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class DataSourceBase(BaseModel):
    """数据源基础字段"""
    name: str = Field(..., max_length=100, description="数据源名称")
    group_id: Optional[str] = Field(None, description="所属分组ID")
    db_type: str = Field(..., description="数据库类型：mysql/oracle/sqlserver/postgresql/dm/inceptor")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口号")
    database: str = Field(..., description="数据库名")
    schema: Optional[str] = Field(None, description="Schema名")
    username: str = Field(..., description="用户名")
    charset: str = Field("UTF-8", description="字符集")
    timeout: int = Field(30, description="连接超时秒数")


class CreateDataSourceRequest(DataSourceBase):
    """创建数据源请求"""
    password: str = Field(..., description="密码")


class UpdateDataSourceRequest(BaseModel):
    """更新数据源请求"""
    name: Optional[str] = Field(None, max_length=100)
    group_id: Optional[str] = None
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    charset: Optional[str] = None
    timeout: Optional[int] = None


class DataSourceResponse(DataSourceBase):
    """数据源响应"""
    id: str
    group_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    """测试连接请求（不保存）"""
    db_type: str
    host: str
    port: int
    database: str
    schema: Optional[str] = None
    username: str
    password: str
    charset: str = "UTF-8"
    timeout: int = 30


class TestConnectionResult(BaseModel):
    """连接测试结果"""
    success: bool
    message: str
    latency: Optional[int] = None
    version: Optional[str] = None


class TableInfo(BaseModel):
    """表信息"""
    name: str
    schema: Optional[str] = None
    comment: Optional[str] = None
    row_count: Optional[int] = None


class ColumnInfo(BaseModel):
    """字段信息"""
    name: str
    data_type: str
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    nullable: bool = True
    default_value: Optional[str] = None
    comment: Optional[str] = None
    is_primary_key: bool = False


class IndexInfo(BaseModel):
    """索引信息"""
    name: str
    columns: List[str]
    is_unique: bool
    is_primary: bool
    index_type: Optional[str] = None


class ConstraintInfo(BaseModel):
    """约束信息"""
    name: str
    constraint_type: str
    columns: List[str]
    reference_table: Optional[str] = None
    reference_columns: Optional[List[str]] = None


class TableSchema(BaseModel):
    """表结构信息"""
    table_name: str
    comment: Optional[str] = None
    columns: List[ColumnInfo]
    indexes: List[IndexInfo]
    constraints: List[ConstraintInfo]


# 数据源分组
class DataSourceGroupBase(BaseModel):
    """分组基础字段"""
    name: str = Field(..., max_length=100)
    sort_order: int = Field(0)


class CreateGroupRequest(BaseModel):
    """创建分组请求"""
    name: str = Field(..., max_length=100)


class UpdateGroupRequest(BaseModel):
    """更新分组请求"""
    name: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = None


class DataSourceGroupResponse(BaseModel):
    """分组响应"""
    id: str
    name: str
    count: int = 0
    sort_order: int
    
    class Config:
        from_attributes = True
