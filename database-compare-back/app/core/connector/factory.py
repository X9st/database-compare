"""连接器工厂"""
from importlib import import_module
from typing import Dict, Tuple, Type

from .base import BaseConnector


class ConnectorFactory:
    """连接器工厂"""

    # 懒加载连接器，避免未使用驱动阻塞其它数据库。
    _connector_specs: Dict[str, Tuple[str, str]] = {
        "mysql": (".mysql", "MySQLConnector"),
        "postgresql": (".postgresql", "PostgreSQLConnector"),
        "oracle": (".oracle", "OracleConnector"),
        "sqlserver": (".sqlserver", "SQLServerConnector"),
        "dm": (".dm", "DMConnector"),
        "inceptor": (".inceptor", "InceptorConnector"),
    }
    _connectors: Dict[str, Type[BaseConnector]] = {}

    @classmethod
    def _load_connector_class(cls, db_type: str) -> Type[BaseConnector]:
        db_type = db_type.lower()

        if db_type in cls._connectors:
            return cls._connectors[db_type]

        if db_type not in cls._connector_specs:
            raise ValueError(
                f"不支持的数据库类型: {db_type}。当前支持: {', '.join(cls.get_supported_types())}"
            )

        module_name, class_name = cls._connector_specs[db_type]
        try:
            module = import_module(module_name, package=__package__)
            connector_class = getattr(module, class_name)
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                f"加载 {db_type} 连接器失败，缺少依赖: {exc.name}"
            ) from exc

        cls._connectors[db_type] = connector_class
        return connector_class

    @classmethod
    def create(cls, db_type: str, **kwargs) -> BaseConnector:
        """创建数据库连接器"""
        connector_class = cls._load_connector_class(db_type)
        return connector_class(**kwargs)

    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的数据库类型"""
        return list(cls._connector_specs.keys())

    @classmethod
    def register(cls, db_type: str, connector_class: Type[BaseConnector]):
        """注册新的连接器类型"""
        cls._connectors[db_type.lower()] = connector_class
