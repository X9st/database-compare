"""数据库连接器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TableInfo:
    """表信息"""
    name: str
    schema: Optional[str] = None
    comment: Optional[str] = None
    row_count: int = 0


@dataclass
class ColumnInfo:
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


@dataclass
class IndexInfo:
    """索引信息"""
    name: str
    columns: List[str]
    is_unique: bool
    is_primary: bool
    index_type: str = "BTREE"


@dataclass
class ConstraintInfo:
    """约束信息"""
    name: str
    constraint_type: str  # PRIMARY KEY, UNIQUE, FOREIGN KEY, CHECK
    columns: List[str]
    reference_table: Optional[str] = None
    reference_columns: Optional[List[str]] = None


class BaseConnector(ABC):
    """数据库连接器基类"""
    
    def __init__(self, host: str, port: int, database: str, 
                 username: str, password: str, schema: str = None,
                 charset: str = "UTF-8", timeout: int = 30,
                 extra_config: Optional[Dict[str, Any]] = None):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.schema = schema
        self.charset = charset
        self.timeout = timeout
        self.extra_config = extra_config or {}
        self.source_kind = "database"
        self._connection = None

    @property
    def is_file_source(self) -> bool:
        return self.source_kind == "file"
    
    @abstractmethod
    def connect(self) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        pass
    
    @abstractmethod
    def get_tables(self) -> List[TableInfo]:
        """获取表列表"""
        pass
    
    @abstractmethod
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        """获取表字段"""
        pass
    
    @abstractmethod
    def get_indexes(self, table_name: str) -> List[IndexInfo]:
        """获取表索引"""
        pass
    
    @abstractmethod
    def get_constraints(self, table_name: str) -> List[ConstraintInfo]:
        """获取表约束"""
        pass
    
    @abstractmethod
    def get_primary_keys(self, table_name: str) -> List[str]:
        """获取主键字段"""
        pass
    
    @abstractmethod
    def get_row_count(self, table_name: str, where_clause: str = None) -> int:
        """获取行数"""
        pass
    
    @abstractmethod
    def fetch_data(self, table_name: str, columns: List[str] = None,
                   where_clause: str = None, order_by: List[str] = None,
                   offset: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取数据"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """获取数据库版本"""
        pass
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
