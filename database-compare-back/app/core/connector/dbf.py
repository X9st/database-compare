"""DBF 文件连接器"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseConnector, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo


class DBFConnector(BaseConnector):
    """DBF 文件连接器（单文件/数据集双模式）"""

    TYPE_MAPPING = {
        "C": "STRING",
        "N": "NUMERIC",
        "F": "FLOAT",
        "D": "DATE",
        "T": "DATETIME",
        "L": "BOOLEAN",
        "M": "TEXT",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source_kind = "file"
        self._mode = "single_file"
        self._storage_path: Optional[Path] = None
        self._table_name: Optional[str] = None
        self._table = None
        self._table_index: Dict[str, Dict[str, Any]] = {}

    def _resolve_mode(self) -> str:
        mode = str((self.extra_config or {}).get("mode") or "").strip().lower()
        if mode:
            return mode
        snapshot = (self.extra_config or {}).get("snapshot")
        if isinstance(snapshot, dict) and isinstance(snapshot.get("table_index"), dict):
            return "remote_dataset"
        return "single_file"

    def _resolve_storage_path(self) -> Path:
        storage_key = str((self.extra_config or {}).get("storage_key") or "").strip()
        if not storage_key:
            raise ConnectionError("DBF 数据源缺少 extra_config.storage_key")
        path = Path(storage_key)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()

    def connect(self) -> bool:
        self._mode = self._resolve_mode()
        if self._mode == "remote_dataset":
            snapshot = (self.extra_config or {}).get("snapshot") or {}
            table_index = snapshot.get("table_index")
            if not isinstance(table_index, dict) or not table_index:
                raise ConnectionError("DBF 远程数据集缺少 snapshot.table_index")
            normalized: Dict[str, Dict[str, Any]] = {}
            for table_name, entry in table_index.items():
                if not isinstance(entry, dict):
                    continue
                file_path = Path(str(entry.get("storage_key") or ""))
                if not file_path.is_absolute():
                    file_path = Path.cwd() / file_path
                file_path = file_path.resolve()
                if not file_path.exists() or not file_path.is_file():
                    raise ConnectionError(f"DBF 数据集文件不存在: {file_path}")
                if file_path.suffix.lower() != ".dbf":
                    raise ConnectionError(f"DBF 数据集文件类型非法: {file_path.name}")
                normalized[str(table_name)] = {**entry, "storage_key": str(file_path.as_posix())}
            if not normalized:
                raise ConnectionError("DBF 远程数据集无可用表")
            self._table_index = normalized
            return True

        path = self._resolve_storage_path()
        if not path.exists() or not path.is_file():
            raise ConnectionError(f"DBF 文件不存在: {path}")
        if path.suffix.lower() != ".dbf":
            raise ConnectionError("DBF 数据源仅支持 .dbf 文件")

        try:
            from dbfread import DBF
        except ImportError as exc:
            raise ConnectionError("未安装 dbfread 驱动，请执行: pip install dbfread") from exc

        self._storage_path = path
        self._table_name = path.stem
        self._table = DBF(str(path), load=True, char_decode_errors="ignore")
        return True

    def disconnect(self) -> None:
        self._table = None
        self._table_index = {}

    def test_connection(self) -> Dict[str, Any]:
        try:
            self.connect()
            version = self.get_version()
            self.disconnect()
            return {"success": True, "message": "连接成功", "version": version}
        except Exception as exc:
            return {"success": False, "message": str(exc), "version": None}

    def _resolve_dataset_entry(self, table_name: str) -> Dict[str, Any]:
        target = str(table_name or "").strip().lower()
        for name, entry in self._table_index.items():
            if name.lower() == target:
                return entry
        raise ValueError(f"表不存在: {table_name}")

    def _ensure_table_name(self, table_name: str) -> None:
        if not self._table_name:
            raise ConnectionError("DBF 未连接")
        if str(table_name or "").strip().lower() != self._table_name.lower():
            raise ValueError(f"DBF 仅包含单表: {self._table_name}")

    def _open_table(self, file_path: Path):
        try:
            from dbfread import DBF
        except ImportError as exc:
            raise ConnectionError("未安装 dbfread 驱动，请执行: pip install dbfread") from exc
        return DBF(str(file_path), load=True, char_decode_errors="ignore")

    def _read_dataset_rows(self, table_name: str) -> List[Dict[str, Any]]:
        entry = self._resolve_dataset_entry(table_name)
        file_path = Path(str(entry.get("storage_key")))
        table = self._open_table(file_path)
        return [dict(item) for item in list(table)]

    def get_tables(self) -> List[TableInfo]:
        if self._mode == "remote_dataset":
            result: List[TableInfo] = []
            for table_name, entry in self._table_index.items():
                rows = self._read_dataset_rows(table_name)
                result.append(
                    TableInfo(
                        name=table_name,
                        schema=str(entry.get("original_name") or Path(str(entry.get("storage_key"))).name),
                        comment="DBF Table",
                        row_count=len(rows),
                    )
                )
            return result

        rows = list(self._table or [])
        return [
            TableInfo(
                name=self._table_name or "dbf_table",
                schema=self._storage_path.name if self._storage_path else None,
                comment="DBF Table",
                row_count=len(rows),
            )
        ]

    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        table_obj = self._table
        if self._mode == "remote_dataset":
            entry = self._resolve_dataset_entry(table_name)
            table_obj = self._open_table(Path(str(entry.get("storage_key"))))
        else:
            self._ensure_table_name(table_name)
        columns: List[ColumnInfo] = []
        for field in getattr(table_obj, "fields", []):
            data_type = self.TYPE_MAPPING.get(str(getattr(field, "type", "")).upper(), "STRING")
            length = getattr(field, "length", None)
            precision = getattr(field, "decimal_count", None)
            columns.append(
                ColumnInfo(
                    name=str(getattr(field, "name", "")),
                    data_type=data_type,
                    length=length if isinstance(length, int) and length > 0 else None,
                    precision=precision if isinstance(precision, int) and precision >= 0 else None,
                    nullable=True,
                    is_primary_key=False,
                )
            )
        return columns

    def get_indexes(self, table_name: str) -> List[IndexInfo]:
        return []

    def get_constraints(self, table_name: str) -> List[ConstraintInfo]:
        return []

    def get_primary_keys(self, table_name: str) -> List[str]:
        return []

    def get_row_count(self, table_name: str, where_clause: str = None) -> int:
        if where_clause:
            raise ValueError("DBF 数据源不支持 where 过滤")
        if self._mode == "remote_dataset":
            return len(self._read_dataset_rows(table_name))
        self._ensure_table_name(table_name)
        return len(list(self._table or []))

    def fetch_data(
        self,
        table_name: str,
        columns: List[str] = None,
        where_clause: str = None,
        order_by: List[str] = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        if where_clause:
            raise ValueError("DBF 数据源不支持 where 过滤")

        if self._mode == "remote_dataset":
            rows = self._read_dataset_rows(table_name)
        else:
            self._ensure_table_name(table_name)
            rows = [dict(item) for item in list(self._table or [])]
        if order_by:
            for key in reversed(order_by):
                field = str(key).split()[0]
                rows = sorted(rows, key=lambda item: (item.get(field) is None, str(item.get(field))))

        sliced = rows[offset : offset + limit]
        if not columns:
            return sliced
        return [{c: row.get(c) for c in columns} for row in sliced]

    def get_version(self) -> str:
        if self._mode == "remote_dataset":
            return "DBF (dataset)"
        return "DBF"
