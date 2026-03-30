"""自定义异常类"""
from typing import Optional, Any, Dict


class AppException(Exception):
    """应用基础异常类"""
    
    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


class DatabaseConnectionError(AppException):
    """数据库连接异常"""
    
    def __init__(self, message: str, db_type: str = None, host: str = None):
        details = {}
        if db_type:
            details['db_type'] = db_type
        if host:
            details['host'] = host
        super().__init__(message, code=1001, details=details)


class DatabaseQueryError(AppException):
    """数据库查询异常"""
    
    def __init__(self, message: str, sql: str = None):
        details = {}
        if sql:
            details['sql'] = sql[:500]  # 限制SQL长度
        super().__init__(message, code=1002, details=details)


class DataSourceNotFoundError(AppException):
    """数据源不存在异常"""
    
    def __init__(self, datasource_id: str):
        super().__init__(
            f"数据源不存在: {datasource_id}",
            code=1003,
            details={'datasource_id': datasource_id}
        )


class TaskNotFoundError(AppException):
    """任务不存在异常"""
    
    def __init__(self, task_id: str):
        super().__init__(
            f"比对任务不存在: {task_id}",
            code=1004,
            details={'task_id': task_id}
        )


class ResultNotFoundError(AppException):
    """结果不存在异常"""
    
    def __init__(self, result_id: str):
        super().__init__(
            f"比对结果不存在: {result_id}",
            code=1005,
            details={'result_id': result_id}
        )


class ValidationError(AppException):
    """参数验证异常"""
    
    def __init__(self, message: str, field: str = None):
        details = {}
        if field:
            details['field'] = field
        super().__init__(message, code=1006, details=details)


class CompareError(AppException):
    """比对过程异常"""
    
    def __init__(self, message: str, table_name: str = None, phase: str = None):
        details = {}
        if table_name:
            details['table_name'] = table_name
        if phase:
            details['phase'] = phase
        super().__init__(message, code=1007, details=details)


class ExportError(AppException):
    """导出异常"""
    
    def __init__(self, message: str, format: str = None):
        details = {}
        if format:
            details['format'] = format
        super().__init__(message, code=1008, details=details)


class PermissionDeniedError(AppException):
    """权限不足异常"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, code=1009)


class ConfigurationError(AppException):
    """配置错误异常"""
    
    def __init__(self, message: str, config_key: str = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        super().__init__(message, code=1010, details=details)


class UnsupportedDatabaseError(AppException):
    """不支持的数据库类型异常"""
    
    def __init__(self, db_type: str):
        supported_types = ['mysql', 'oracle', 'dm', 'inceptor', 'excel', 'dbf']
        super().__init__(
            f"不支持的数据库类型: {db_type}。支持的类型: {', '.join(supported_types)}",
            code=1011,
            details={'db_type': db_type, 'supported_types': supported_types}
        )


class TaskCancelledError(AppException):
    """任务被取消异常"""
    
    def __init__(self, task_id: str):
        super().__init__(
            f"任务已被取消: {task_id}",
            code=1012,
            details={'task_id': task_id}
        )


class TaskAlreadyRunningError(AppException):
    """任务已在运行异常"""
    
    def __init__(self, task_id: str):
        super().__init__(
            f"任务已在运行中: {task_id}",
            code=1013,
            details={'task_id': task_id}
        )
