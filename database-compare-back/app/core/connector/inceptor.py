"""Inceptor数据库连接器"""
import re
from typing import List, Dict, Any, Optional
from .base import BaseConnector, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo


class InceptorConnector(BaseConnector):
    """Inceptor数据库连接器 (基于Hive兼容驱动)"""

    _SUPPORTED_AUTH_MODES = {"LDAP", "NONE", "NOSASL", "CUSTOM"}
    _SUPPORTED_TRANSPORT_MODES = {"BINARY", "HTTP", "HTTPS"}
    
    def __init__(self, host: str, port: int, database: str,
                 username: str, password: str, schema: str = None,
                 charset: str = "UTF-8", timeout: int = 30,
                 extra_config: Optional[Dict[str, Any]] = None):
        super().__init__(
            host,
            port,
            database,
            username,
            password,
            schema,
            charset,
            timeout,
            extra_config=extra_config,
        )
        self._cursor = None
    
    def connect(self) -> bool:
        """建立连接"""
        try:
            from pyhive import hive

            attempt_errors: List[str] = []
            auth_modes = self._resolve_auth_modes()
            transport_modes = self._resolve_transport_modes()
            for transport_mode in transport_modes:
                for auth_mode in auth_modes:
                    effective_auth = self._effective_auth_mode(
                        auth_mode=auth_mode,
                        transport_mode=transport_mode,
                    )
                    if not effective_auth:
                        continue
                    attempt_label = f"{transport_mode}/{auth_mode}"
                    if effective_auth != auth_mode:
                        attempt_label = f"{attempt_label}->{effective_auth}"
                    try:
                        self._connection = self._connect_with_mode(
                            hive=hive,
                            transport_mode=transport_mode,
                            effective_auth_mode=effective_auth,
                        )
                        self._apply_transport_timeout(self._connection)
                        self._cursor = self._connection.cursor()
                        return True
                    except Exception as exc:
                        attempt_errors.append(f"{attempt_label}: {exc}")
                        self._connection = None
                        self._cursor = None
            raise ConnectionError(self._build_connection_error(auth_modes, transport_modes, attempt_errors))
        except ImportError:
            raise ConnectionError("未安装pyhive驱动，请执行: pip install pyhive")
        except Exception as e:
            raise ConnectionError(f"Inceptor连接失败: {str(e)}")

    def _normalize_transport_mode(self, mode: Any) -> Optional[str]:
        raw = str(mode or "").strip().upper()
        if not raw:
            return None
        return raw if raw in self._SUPPORTED_TRANSPORT_MODES else None

    def _apply_transport_timeout(self, connection: Any) -> None:
        """尽力设置底层传输超时，避免查询无限阻塞。"""
        timeout_ms = max(1, int(self.timeout or 30)) * 1000
        timeout_sec = timeout_ms / 1000.0
        transport = getattr(connection, "_transport", None)
        if not transport:
            return

        candidates = [
            transport,
            getattr(transport, "_trans", None),
            getattr(getattr(transport, "_trans", None), "_trans", None),
            getattr(getattr(transport, "_trans", None), "_socket", None),
            getattr(getattr(getattr(transport, "_trans", None), "_trans", None), "_socket", None),
            getattr(getattr(transport, "_trans", None), "handle", None),
        ]
        for obj in candidates:
            if obj is None:
                continue
            try:
                if hasattr(obj, "setTimeout"):
                    obj.setTimeout(timeout_ms)
                if hasattr(obj, "settimeout"):
                    obj.settimeout(timeout_sec)
            except Exception:
                continue

    @staticmethod
    def _as_mode_list(raw_modes: Any) -> List[str]:
        if isinstance(raw_modes, str):
            return [item.strip() for item in raw_modes.split(",")]
        if isinstance(raw_modes, list):
            return [str(item).strip() for item in raw_modes]
        return []

    def _resolve_transport_modes(self) -> List[str]:
        extra = self.extra_config or {}
        preferred = self._normalize_transport_mode(
            extra.get("inceptor_transport_mode") or extra.get("transport_mode")
        )
        fallback_raw = (
            extra.get("inceptor_transport_fallback_modes")
            or extra.get("transport_fallback_modes")
            or []
        )
        fallback_modes = self._as_mode_list(fallback_raw)
        result: List[str] = []
        for mode in [preferred, *fallback_modes]:
            normalized = self._normalize_transport_mode(mode)
            if normalized and normalized not in result:
                result.append(normalized)
        if result:
            return result
        # 自动模式下默认先尝试二进制协议，再回退到 HTTP，覆盖公网网关常见场景。
        return ["BINARY", "HTTP"]

    @staticmethod
    def _effective_auth_mode(auth_mode: str, transport_mode: str) -> Optional[str]:
        if transport_mode == "BINARY":
            return auth_mode
        # Hive HTTP 协议下 pyhive 使用 BASIC 代替 LDAP。
        if auth_mode == "LDAP":
            return "BASIC"
        if auth_mode == "CUSTOM":
            return None
        return auth_mode

    @staticmethod
    def _coerce_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        raw = str(value or "").strip().lower()
        if not raw:
            return default
        return raw in {"1", "true", "yes", "on"}

    def _connect_with_mode(self, hive, transport_mode: str, effective_auth_mode: str):
        """按认证模式与传输模式建立连接。"""
        kwargs: Dict[str, Any] = {
            "username": self.username,
            "database": self.database or "default",
        }
        if transport_mode == "BINARY":
            kwargs.update({
                "host": self.host,
                "port": self.port,
                "auth": effective_auth_mode,
            })
            # pyhive 对 NONE/NOSASL 模式不接受 password 入参。
            if effective_auth_mode in {"LDAP", "CUSTOM"} and self.password:
                kwargs["password"] = self.password
            return hive.connect(**kwargs)

        kwargs.update({
            "host": self.host,
            "port": self.port,
            "scheme": transport_mode.lower(),
            "auth": effective_auth_mode,
        })
        if self.password:
            kwargs["password"] = self.password
        if transport_mode == "HTTPS":
            extra = self.extra_config or {}
            kwargs["check_hostname"] = "true" if self._coerce_bool(
                extra.get("inceptor_ssl_check_hostname") or extra.get("ssl_check_hostname"),
                default=False,
            ) else "false"
            ssl_cert = str(
                extra.get("inceptor_ssl_cert") or extra.get("ssl_cert") or ""
            ).strip().lower()
            if ssl_cert in {"none", "optional", "required"}:
                kwargs["ssl_cert"] = ssl_cert
        return hive.connect(**kwargs)

    def _normalize_auth_mode(self, mode: Any) -> Optional[str]:
        raw = str(mode or "").strip().upper()
        if not raw:
            return None
        return raw if raw in self._SUPPORTED_AUTH_MODES else None

    def _resolve_auth_modes(self) -> List[str]:
        """解析连接时的认证模式（支持显式配置+回退）。"""
        extra = self.extra_config or {}
        preferred = self._normalize_auth_mode(
            extra.get("inceptor_auth_mode") or extra.get("auth_mode")
        )

        fallback_raw = (
            extra.get("inceptor_auth_fallback_modes")
            or extra.get("auth_fallback_modes")
            or []
        )
        fallback_modes = self._as_mode_list(fallback_raw)

        result: List[str] = []
        for mode in [preferred, *fallback_modes]:
            normalized = self._normalize_auth_mode(mode)
            if normalized and normalized not in result:
                result.append(normalized)
        if result:
            return result
        # 仅在自动模式下使用默认回退链路。
        return ["LDAP", "NOSASL", "NONE"] if self.password else ["NONE", "NOSASL", "LDAP"]

    def _build_connection_error(
        self,
        auth_modes: List[str],
        transport_modes: List[str],
        attempt_errors: List[str],
    ) -> str:
        attempt_text = "; ".join(attempt_errors) if attempt_errors else "未知错误"
        proxy_hint = ""
        if any("Tunnel connection failed" in err for err in attempt_errors):
            proxy_hint = (
                " 检测到 HTTP 代理隧道失败（Tunnel connection failed），"
                "请检查运行后端进程所在机器的代理环境变量（HTTP_PROXY/HTTPS_PROXY），"
                "并将 Inceptor 主机加入 NO_PROXY。"
            )
        if any("TSocket read 0 bytes" in err for err in attempt_errors):
            return (
                "连接被服务端中断（TSocket read 0 bytes）。"
                f"已尝试认证模式: {', '.join(auth_modes)}。"
                f"已尝试传输模式: {', '.join(transport_modes)}。"
                "请检查 Inceptor 认证模式/传输模式与项目配置是否一致，"
                "可在数据源 extra_config 中设置 inceptor_auth_mode"
                "（LDAP/NOSASL/NONE/CUSTOM）、inceptor_auth_fallback_modes、"
                "inceptor_transport_mode（BINARY/HTTP/HTTPS）及 inceptor_transport_fallback_modes；"
                "若客户端在公网环境，建议使用 SSH 隧道转发到服务器 127.0.0.1:10000。"
                f"{proxy_hint} 详细错误: {attempt_text}"
            )
        return (
            f"连接失败，已尝试认证模式 {', '.join(auth_modes)}，"
            f"传输模式 {', '.join(transport_modes)}，错误: {attempt_text}"
            f"{proxy_hint}"
        )
    
    def disconnect(self) -> None:
        """断开连接"""
        if self._cursor:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._cursor = None
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            self.connect()
            version = self.get_version()
            self.disconnect()
            return {
                "success": True,
                "message": "连接成功",
                "version": version
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "version": None
            }
    
    def get_tables(self) -> List[TableInfo]:
        """获取表列表"""
        self._cursor.execute("SHOW TABLES")
        results = self._cursor.fetchall()
        
        tables = []
        for row in results:
            table_name = row[0]
            # 获取表注释
            try:
                self._cursor.execute(f"DESCRIBE FORMATTED {table_name}")
                desc_results = self._cursor.fetchall()
                comment = None
                for desc_row in desc_results:
                    if desc_row[0] and 'Table Parameters' in str(desc_row[0]):
                        continue
                    if desc_row[0] and 'comment' in str(desc_row[0]).lower():
                        comment = desc_row[1] if len(desc_row) > 1 else None
                        break
            except:
                comment = None
            
            tables.append(TableInfo(
                name=table_name,
                schema=self.database,
                comment=comment,
                row_count=0  # Inceptor获取行数成本高，默认为0
            ))
        return tables
    
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        """获取表字段"""
        primary_keys = {pk.lower() for pk in self.get_primary_keys(table_name)}
        self._cursor.execute(f"DESCRIBE {table_name}")
        results = self._cursor.fetchall()
        
        columns = []
        is_partition_section = False
        
        for row in results:
            col_name = row[0].strip() if row[0] else ''
            
            # 跳过分区信息部分
            if col_name.startswith('#') or col_name == '' or 'Partition' in col_name:
                if 'Partition' in col_name:
                    is_partition_section = True
                continue
            
            if is_partition_section:
                continue
            
            data_type = row[1].strip() if len(row) > 1 and row[1] else 'string'
            comment = row[2].strip() if len(row) > 2 and row[2] else None
            
            # 解析数据类型和长度
            length = None
            precision = None
            scale = None
            
            if '(' in data_type:
                type_name = data_type.split('(')[0]
                params = data_type.split('(')[1].rstrip(')')
                if ',' in params:
                    precision = int(params.split(',')[0])
                    scale = int(params.split(',')[1])
                else:
                    length = int(params)
                data_type = type_name
            
            columns.append(ColumnInfo(
                name=col_name,
                data_type=data_type,
                length=length,
                precision=precision,
                scale=scale,
                nullable=True,  # Hive/Inceptor 默认允许空值
                default_value=None,
                comment=comment,
                is_primary_key=col_name.lower() in primary_keys
            ))
        return columns
    
    def get_indexes(self, table_name: str) -> List[IndexInfo]:
        """获取表索引 (Inceptor不支持传统索引)"""
        return []
    
    def get_constraints(self, table_name: str) -> List[ConstraintInfo]:
        """获取表约束（仅尽力识别主键）"""
        primary_keys = self.get_primary_keys(table_name)
        if not primary_keys:
            return []
        return [ConstraintInfo(
            name=f"{table_name}_pk",
            constraint_type="PRIMARY KEY",
            columns=primary_keys
        )]
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """获取主键字段（尽力从DDL解析）"""
        ddl_text = self._get_table_ddl_text(table_name)
        if not ddl_text:
            return []
        return self._parse_primary_keys_from_ddl(ddl_text)
    
    def get_row_count(self, table_name: str, where_clause: str = None) -> int:
        """获取行数"""
        sql = f"SELECT COUNT(*) FROM {table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        self._cursor.execute(sql)
        result = self._cursor.fetchone()
        return result[0] if result else 0
    
    def fetch_data(self, table_name: str, columns: List[str] = None,
                   where_clause: str = None, order_by: List[str] = None,
                   offset: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取数据"""
        cols = ', '.join([f'`{c}`' for c in columns]) if columns else '*'
        sql = f"SELECT {cols} FROM {table_name}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {', '.join(order_by)}"

        rows = []
        if offset > 0:
            # 优先使用 LIMIT offset, size；不支持时回退为 LIMIT offset+size 再在内存截断。
            paged_sql = f"{sql} LIMIT {offset}, {limit}"
            try:
                self._cursor.execute(paged_sql)
                rows = self._cursor.fetchall()
            except Exception:
                fallback_sql = f"{sql} LIMIT {offset + limit}"
                self._cursor.execute(fallback_sql)
                rows = self._cursor.fetchall()[offset:offset + limit]
        else:
            self._cursor.execute(f"{sql} LIMIT {limit}")
            rows = self._cursor.fetchall()
        
        # 获取列名
        if columns:
            col_names = columns
        else:
            col_names = [desc[0] for desc in self._cursor.description]
        
        return [dict(zip(col_names, row)) for row in rows]
    
    def get_version(self) -> str:
        """获取数据库版本"""
        try:
            self._cursor.execute("SELECT version()")
            result = self._cursor.fetchone()
            return result[0] if result else "Unknown"
        except:
            return "Inceptor"

    def _get_table_ddl_text(self, table_name: str) -> str:
        """获取建表DDL文本"""
        try:
            self._cursor.execute(f"SHOW CREATE TABLE {table_name}")
            rows = self._cursor.fetchall()
        except Exception:
            return ""

        ddl_lines = []
        for row in rows:
            for cell in row:
                if cell is None:
                    continue
                text = str(cell).strip()
                if text:
                    ddl_lines.append(text)
        return "\n".join(ddl_lines)

    def _parse_primary_keys_from_ddl(self, ddl_text: str) -> List[str]:
        """从DDL中解析主键列"""
        # 示例:
        # PRIMARY KEY (`id`)
        # CONSTRAINT pk_x PRIMARY KEY (id1, id2) DISABLE NOVALIDATE
        match = re.search(r"PRIMARY\s+KEY\s*\((.*?)\)", ddl_text, re.IGNORECASE | re.DOTALL)
        if not match:
            return []

        raw_cols = match.group(1)
        cols = []
        for item in raw_cols.split(","):
            col = item.strip().strip("`").strip('"')
            if col:
                cols.append(col)
        return cols
