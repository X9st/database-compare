"""数据源相关Schema"""
from typing import Optional, List, Dict, Any, ClassVar, Set
from pydantic import BaseModel, Field, model_validator
from datetime import datetime


class DataSourceBase(BaseModel):
    """数据源基础字段"""
    SUPPORTED_DB_TYPES: ClassVar[Set[str]] = {"mysql", "oracle", "dm", "inceptor", "excel", "dbf"}
    FILE_DB_TYPES: ClassVar[Set[str]] = {"excel", "dbf"}
    FILE_MODES: ClassVar[Set[str]] = {"single_file", "remote_dataset"}

    name: str = Field(..., max_length=100, description="数据源名称")
    group_id: Optional[str] = Field(None, description="所属分组ID")
    db_type: str = Field(..., description="数据库类型：mysql/oracle/dm/inceptor/excel/dbf")
    host: Optional[str] = Field(None, description="主机地址")
    port: Optional[int] = Field(None, description="端口号")
    database: Optional[str] = Field(None, description="数据库名")
    schema: Optional[str] = Field(None, description="Schema名")
    username: Optional[str] = Field(None, description="用户名")
    charset: str = Field("UTF-8", description="字符集")
    timeout: int = Field(30, description="连接超时秒数")
    extra_config: Optional[Dict[str, Any]] = Field(
        None,
        description="扩展配置（文件源: single_file 或 remote_dataset）",
    )

    @classmethod
    def _validate_single_file_config(cls, db_type: str, extra_config: Dict[str, Any]) -> None:
        storage_key = str(extra_config.get("storage_key") or "").strip()
        file_type = str(extra_config.get("file_type") or "").strip().lower()
        if not storage_key:
            raise ValueError("文件数据源缺少 storage_key")
        if file_type not in {"xlsx", "xls", "dbf"}:
            raise ValueError("文件数据源 file_type 仅支持 xlsx/xls/dbf")
        if db_type == "excel" and file_type not in {"xlsx", "xls"}:
            raise ValueError("excel 数据源的 file_type 必须是 xlsx/xls")
        if db_type == "dbf" and file_type != "dbf":
            raise ValueError("dbf 数据源的 file_type 必须是 dbf")

    @classmethod
    def _validate_remote_dataset_config(
        cls,
        db_type: str,
        extra_config: Dict[str, Any],
        require_plain_password: bool = False,
    ) -> None:
        sftp = extra_config.get("sftp")
        if not isinstance(sftp, dict):
            raise ValueError("远程数据集缺少 extra_config.sftp 配置")

        host = str(sftp.get("host") or "").strip()
        username = str(sftp.get("username") or "").strip()
        base_dir = str(sftp.get("base_dir") or "").strip()
        if not host or not username or not base_dir:
            raise ValueError("远程数据集缺少 sftp.host/username/base_dir")

        try:
            port = int(sftp.get("port") or 22)
        except Exception as exc:
            raise ValueError("远程数据集 sftp.port 非法") from exc
        if port <= 0 or port > 65535:
            raise ValueError("远程数据集 sftp.port 必须在 1-65535 之间")

        plain_password = str(sftp.get("password") or "").strip()
        encrypted_password = str(sftp.get("password_encrypted") or "").strip()
        if require_plain_password:
            if not plain_password:
                raise ValueError("远程数据集必须提供 sftp.password")
        elif not plain_password and not encrypted_password:
            snapshot = extra_config.get("snapshot")
            if not isinstance(snapshot, dict):
                raise ValueError("远程数据集必须提供 sftp.password 或 sftp.password_encrypted")

        declared_file_type = str(extra_config.get("file_type") or "").strip().lower()
        if declared_file_type:
            if db_type == "excel" and declared_file_type not in {"xlsx", "xls"}:
                raise ValueError("excel 远程数据集 file_type 必须是 xlsx/xls")
            if db_type == "dbf" and declared_file_type != "dbf":
                raise ValueError("dbf 远程数据集 file_type 必须是 dbf")

    @model_validator(mode="after")
    def validate_fields_by_db_type(self) -> "DataSourceBase":
        db_type = (self.db_type or "").strip().lower()
        if db_type not in self.SUPPORTED_DB_TYPES:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        self.db_type = db_type
        if db_type in self.FILE_DB_TYPES:
            if not isinstance(self.extra_config, dict):
                raise ValueError("文件数据源必须提供 extra_config")
            mode = str(self.extra_config.get("mode") or "").strip().lower()
            if not mode:
                mode = "remote_dataset" if isinstance(self.extra_config.get("sftp"), dict) else "single_file"
                self.extra_config["mode"] = mode

            if mode not in self.FILE_MODES:
                raise ValueError(f"文件数据源 mode 仅支持: {', '.join(sorted(self.FILE_MODES))}")

            if mode == "single_file":
                self._validate_single_file_config(db_type=db_type, extra_config=self.extra_config)
            else:
                self._validate_remote_dataset_config(db_type=db_type, extra_config=self.extra_config)
        else:
            required = {
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "username": self.username,
            }
            missing = [k for k, v in required.items() if v in (None, "")]
            if missing:
                raise ValueError(f"数据库数据源缺少必填字段: {', '.join(missing)}")
        return self


class CreateDataSourceRequest(DataSourceBase):
    """创建数据源请求"""
    password: Optional[str] = Field(None, description="密码")

    @model_validator(mode="after")
    def validate_password(self) -> "CreateDataSourceRequest":
        if self.db_type not in self.FILE_DB_TYPES and not self.password:
            raise ValueError("数据库数据源必须提供密码")
        return self


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
    extra_config: Optional[Dict[str, Any]] = None


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
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    charset: str = "UTF-8"
    timeout: int = 30
    extra_config: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_test_request(self) -> "TestConnectionRequest":
        db_type = (self.db_type or "").strip().lower()
        if db_type not in DataSourceBase.SUPPORTED_DB_TYPES:
            raise ValueError(f"不支持的数据库类型: {db_type}")
        self.db_type = db_type
        if db_type in DataSourceBase.FILE_DB_TYPES:
            if not isinstance(self.extra_config, dict):
                raise ValueError("文件数据源测试连接必须提供 extra_config")
            mode = str(self.extra_config.get("mode") or "").strip().lower()
            if not mode:
                mode = "remote_dataset" if isinstance(self.extra_config.get("sftp"), dict) else "single_file"
                self.extra_config["mode"] = mode
            if mode == "single_file":
                DataSourceBase._validate_single_file_config(db_type=db_type, extra_config=self.extra_config)
            elif mode == "remote_dataset":
                DataSourceBase._validate_remote_dataset_config(
                    db_type=db_type,
                    extra_config=self.extra_config,
                    require_plain_password=True,
                )
            else:
                raise ValueError("文件数据源测试连接 mode 非法")
            return self

        required = {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": self.password,
        }
        missing = [k for k, v in required.items() if v in (None, "")]
        if missing:
            raise ValueError(f"数据库测试连接缺少必填字段: {', '.join(missing)}")
        return self


class TestConnectionResult(BaseModel):
    """连接测试结果"""
    success: bool
    message: str
    latency: Optional[int] = None
    version: Optional[str] = None


class FileUploadResponse(BaseModel):
    """数据源文件上传响应"""
    file_id: str
    storage_key: str
    original_name: str
    file_type: str
    file_size: int


class CreateRemoteDatasetRequest(BaseModel):
    """创建远程目录数据集请求"""
    name: str = Field(..., max_length=100, description="数据源名称")
    group_id: Optional[str] = Field(None, description="所属分组ID")
    db_type: str = Field(..., description="文件族类型：excel/dbf")
    database: Optional[str] = Field(None, description="数据集名称")
    charset: str = Field("UTF-8", description="字符集")
    timeout: int = Field(30, description="连接超时秒数")
    extra_config: Dict[str, Any] = Field(..., description="远程数据集配置")

    @model_validator(mode="after")
    def validate_remote_dataset(self) -> "CreateRemoteDatasetRequest":
        db_type = (self.db_type or "").strip().lower()
        if db_type not in DataSourceBase.FILE_DB_TYPES:
            raise ValueError("远程目录数据集仅支持 excel/dbf")
        self.db_type = db_type

        if not isinstance(self.extra_config, dict):
            raise ValueError("远程目录数据集必须提供 extra_config")

        mode = str(self.extra_config.get("mode") or "").strip().lower() or "remote_dataset"
        if mode != "remote_dataset":
            raise ValueError("远程目录数据集 extra_config.mode 必须为 remote_dataset")
        self.extra_config["mode"] = "remote_dataset"

        DataSourceBase._validate_remote_dataset_config(
            db_type=db_type,
            extra_config=self.extra_config,
            require_plain_password=True,
        )
        return self


class RemoteDatasetRefreshResponse(BaseModel):
    """远程目录数据集刷新响应"""
    datasource_id: str
    file_count: int
    table_count: int
    failed_files: List[Dict[str, Any]] = Field(default_factory=list)
    last_refresh_at: datetime


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
