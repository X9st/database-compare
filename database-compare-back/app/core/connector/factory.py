"""连接器工厂"""
from typing import Dict, Type
from .base import BaseConnector
from .mysql import MySQLConnector
from .postgresql import PostgreSQLConnector
from .oracle import OracleConnector
from .sqlserver import SQLServerConnector
from .dm import DMConnector
from .inceptor import InceptorConnector


class ConnectorFactory:
    """连接器工厂"""
    
    _connectors: Dict[str, Type[BaseConnector]] = {
        'mysql': MySQLConnector,
        'postgresql': PostgreSQLConnector,
        'oracle': OracleConnector,
        'sqlserver': SQLServerConnector,
        'dm': DMConnector,
        'inceptor': InceptorConnector,
    }
    
    @classmethod
    def create(cls, db_type: str, **kwargs) -> BaseConnector:
        """创建数据库连接器"""
        connector_class = cls._connectors.get(db_type.lower())
        if not connector_class:
            raise ValueError(f"不支持的数据库类型: {db_type}。当前支持: {', '.join(cls._connectors.keys())}")
        return connector_class(**kwargs)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的数据库类型"""
        return list(cls._connectors.keys())
    
    @classmethod
    def register(cls, db_type: str, connector_class: Type[BaseConnector]):
        """注册新的连接器类型"""
        cls._connectors[db_type.lower()] = connector_class
