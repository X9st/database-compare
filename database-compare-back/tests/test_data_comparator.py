"""DataComparator 回归测试"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.core.comparator.data import DataComparator, DataDiffType
from app.core.connector.base import ColumnInfo


class StubConnector:
    def __init__(self, columns: List[ColumnInfo], rows: List[Dict[str, Any]]):
        self._columns = columns
        self._rows = rows
        self.fetch_limits: List[int] = []

    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        return self._columns

    def fetch_data(self, table_name: str, columns: Optional[List[str]] = None,
                   where_clause: str = None, order_by: List[str] = None,
                   offset: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        self.fetch_limits.append(limit)
        rows = list(self._rows)

        if where_clause:
            rows = self._apply_where(rows, where_clause)

        if order_by:
            rows.sort(key=lambda row: tuple(row.get(col) for col in order_by))

        rows = rows[offset: offset + limit]
        if not columns:
            return [dict(row) for row in rows]

        return [{col: row.get(col) for col in columns} for row in rows]

    def _apply_where(self, rows: List[Dict[str, Any]], where_clause: str) -> List[Dict[str, Any]]:
        or_clauses = [part.strip() for part in where_clause.split(" OR ")]
        filtered = []
        for row in rows:
            if any(self._matches_clause(row, clause) for clause in or_clauses):
                filtered.append(row)
        return filtered

    def _matches_clause(self, row: Dict[str, Any], clause: str) -> bool:
        clause = clause.strip()
        if clause.endswith("IS NULL"):
            col = clause[:-7].strip()
            return row.get(col) is None

        match = re.match(r"^([a-zA-Z0-9_]+)\s+IN\s*\((.*)\)$", clause)
        if not match:
            return False

        col = match.group(1)
        raw_values = match.group(2)
        values = [self._parse_literal(v.strip()) for v in raw_values.split(",") if v.strip()]
        return row.get(col) in values

    def _parse_literal(self, value: str) -> Any:
        if value.upper() == "NULL":
            return None
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1].replace("''", "'")
        try:
            return int(value)
        except ValueError:
            return value


def test_compare_data_uses_common_columns_when_structure_diff_exists():
    source_columns = [
        ColumnInfo(name="id", data_type="int"),
        ColumnInfo(name="username", data_type="varchar"),
        ColumnInfo(name="email", data_type="varchar"),
        ColumnInfo(name="age", data_type="int"),
        ColumnInfo(name="created_at", data_type="datetime"),
        ColumnInfo(name="status", data_type="int"),
    ]
    target_columns = [
        ColumnInfo(name="id", data_type="int"),
        ColumnInfo(name="username", data_type="varchar"),
        ColumnInfo(name="email", data_type="varchar"),
        ColumnInfo(name="phone", data_type="varchar"),
        ColumnInfo(name="birth_year", data_type="int"),
        ColumnInfo(name="created_at", data_type="datetime"),
        ColumnInfo(name="status", data_type="int"),
    ]

    source_rows = [
        {"id": 1, "username": "zhangsan", "email": "zhangsan@example.com", "age": 25, "created_at": "2026-03-19 08:55:53", "status": 1},
        {"id": 2, "username": "lisi", "email": "lisi@example.com", "age": 30, "created_at": "2026-03-19 08:55:53", "status": 1},
        {"id": 3, "username": "wangwu", "email": "wangwu@example.com", "age": 28, "created_at": "2026-03-19 08:55:53", "status": 1},
        {"id": 4, "username": "zhaoliu", "email": "zhaoliu@example.com", "age": 35, "created_at": "2026-03-19 08:55:53", "status": 0},
        {"id": 5, "username": "qianqi", "email": "qianqi@example.com", "age": 22, "created_at": "2026-03-19 08:55:53", "status": 1},
    ]
    target_rows = [
        {"id": 1, "username": "zhangsan", "email": "zhangsan@example.com", "phone": "13800138001", "birth_year": 1999, "created_at": "2026-03-19 08:55:53", "status": 1},
        {"id": 2, "username": "lisi", "email": "lisi@example.com", "phone": "13800138002", "birth_year": 1994, "created_at": "2026-03-19 08:55:53", "status": 1},
        {"id": 3, "username": "wangwu", "email": "wangwu@example.com", "phone": "13800138003", "birth_year": 1996, "created_at": "2026-03-19 08:55:53", "status": 1},
        {"id": 4, "username": "zhaoliu", "email": "zhaoliu@example.com", "phone": "13800138004", "birth_year": 1989, "created_at": "2026-03-19 08:55:53", "status": 0},
        {"id": 5, "username": "sunba", "email": "sunba@example.com", "phone": "13800138005", "birth_year": 2000, "created_at": "2026-03-19 08:55:53", "status": 1},
    ]

    comparator = DataComparator(
        StubConnector(source_columns, source_rows),
        StubConnector(target_columns, target_rows),
        {"page_size": 1000},
    )

    diffs = comparator.compare_data("users", ["id"])

    assert len(diffs) == 1
    assert diffs[0].primary_key == {"id": 5}
    assert diffs[0].diff_type == DataDiffType.VALUE_DIFF
    assert set(diffs[0].diff_columns) == {"username", "email"}
    assert "age" not in diffs[0].diff_columns


def test_compare_data_target_lookup_not_limited_to_default_1000_rows():
    row_count = 1200
    source_rows = [{"id": i, "username": f"user-{i}"} for i in range(1, row_count + 1)]
    target_rows = [{"id": i, "username": f"user-{i}"} for i in range(1, row_count + 1)]

    columns = [
        ColumnInfo(name="id", data_type="int"),
        ColumnInfo(name="username", data_type="varchar"),
    ]
    source = StubConnector(columns, source_rows)
    target = StubConnector(columns, target_rows)

    comparator = DataComparator(source, target, {"page_size": row_count})
    diffs = comparator.compare_data("users", ["id"], max_diffs=row_count)

    assert diffs == []
    assert row_count in target.fetch_limits
