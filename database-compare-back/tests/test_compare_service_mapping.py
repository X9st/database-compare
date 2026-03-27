"""CompareService 映射模式测试"""
from __future__ import annotations

import pytest

from app.core.connector.base import TableInfo
from app.services.compare_service import CompareService


class StubConnector:
    def __init__(self, tables: list[str]):
        self._tables = tables

    def get_tables(self):
        return [TableInfo(name=t) for t in self._tables]


def _build_service() -> CompareService:
    return CompareService(db=None)  # _build_compare_plan 不依赖数据库会话


def test_build_compare_plan_mapping_mode_success():
    service = _build_service()
    source_conn = StubConnector(["users", "orders"])
    target_conn = StubConnector(["members", "orders_bak"])

    config = {
        "table_selection": {"mode": "mapping", "tables": []},
        "options": {
            "table_mappings": [
                {
                    "source_table": "users",
                    "target_table": "members",
                    "column_mappings": [
                        {"source_column": "id", "target_column": "uid"},
                        {"source_column": "username", "target_column": "name"}
                    ]
                }
            ]
        }
    }

    plan = service._build_compare_plan(source_conn, target_conn, config)
    assert len(plan) == 1
    assert plan[0]["source_table"] == "users"
    assert plan[0]["target_table"] == "members"
    assert plan[0]["display_table"] == "users -> members"
    assert plan[0]["column_mapping"] == {"id": "uid", "username": "name"}


def test_build_compare_plan_mapping_mode_requires_mappings():
    service = _build_service()
    source_conn = StubConnector(["users"])
    target_conn = StubConnector(["members"])

    config = {
        "table_selection": {"mode": "mapping", "tables": []},
        "options": {"table_mappings": []}
    }

    with pytest.raises(ValueError, match="至少一组表映射"):
        service._build_compare_plan(source_conn, target_conn, config)


def test_build_compare_plan_mapping_mode_rejects_duplicate_source_table():
    service = _build_service()
    source_conn = StubConnector(["users"])
    target_conn = StubConnector(["members", "members_bak"])

    config = {
        "table_selection": {"mode": "mapping", "tables": []},
        "options": {
            "table_mappings": [
                {"source_table": "users", "target_table": "members"},
                {"source_table": "users", "target_table": "members_bak"}
            ]
        }
    }

    with pytest.raises(ValueError, match="重复映射"):
        service._build_compare_plan(source_conn, target_conn, config)


def test_build_compare_plan_legacy_include_mode_compatible():
    service = _build_service()
    source_conn = StubConnector(["users", "orders"])
    target_conn = StubConnector(["users", "orders"])

    config = {
        "table_selection": {"mode": "include", "tables": ["users", "not_exist"]},
        "options": {"table_mappings": []}
    }

    plan = service._build_compare_plan(source_conn, target_conn, config)
    assert len(plan) == 1
    assert plan[0]["source_table"] == "users"
    assert plan[0]["target_table"] == "users"
    assert plan[0]["display_table"] == "users"
    assert plan[0]["column_mapping"] == {}


def test_incremental_where_clause_supports_time_and_batch_with_mapping():
    service = _build_service()
    options = {
        "mode": "incremental",
        "incremental_config": {
            "time_column": "created_at",
            "start_time": "2026-01-01 00:00:00",
            "end_time": "2026-01-31 23:59:59",
            "batch_column": "batch_no",
            "batch_value": "B202601",
        }
    }
    mapping = {"created_at": "created_time", "batch_no": "batch_id"}

    source_where, target_where = service._build_incremental_where_clauses(
        options, "orders_src", "orders_tgt", mapping
    )

    assert "created_at >=" in source_where
    assert "created_at <=" in source_where
    assert "batch_no = 'B202601'" in source_where
    assert "created_time >=" in target_where
    assert "created_time <=" in target_where
    assert "batch_id = 'B202601'" in target_where


def test_validate_incremental_config_requires_time_or_batch_filter():
    service = _build_service()
    invalid_config = {
        "options": {
            "mode": "incremental",
            "incremental_config": {
                "start_time": "2026-01-01 00:00:00",
            }
        }
    }

    with pytest.raises(ValueError, match="时间字段或批次字段"):
        service._validate_incremental_config(invalid_config)


def test_validate_incremental_config_allows_batch_only():
    service = _build_service()
    batch_only_config = {
        "options": {
            "mode": "incremental",
            "incremental_config": {
                "batch_column": "batch_no",
                "batch_value": "B202603",
            }
        }
    }

    service._validate_incremental_config(batch_only_config)


def test_resolve_primary_keys_uses_business_key_fallback():
    service = _build_service()

    class NoPkSourceConnector:
        @staticmethod
        def get_primary_keys(_table):
            return []

    options = {
        "table_primary_keys": [
            {
                "source_table": "orders_src",
                "target_table": "orders_tgt",
                "primary_keys": ["order_id", "line_id"],
                "target_primary_keys": ["id", "line_no"],
            }
        ]
    }

    primary_keys, pk_mapping, error = service._resolve_primary_keys(
        source_conn=NoPkSourceConnector(),
        options=options,
        source_table="orders_src",
        target_table="orders_tgt",
    )

    assert error is None
    assert primary_keys == ["order_id", "line_id"]
    assert pk_mapping == {"order_id": "id", "line_id": "line_no"}


def test_resolve_primary_keys_rejects_mismatched_target_key_count():
    service = _build_service()

    class NoPkSourceConnector:
        @staticmethod
        def get_primary_keys(_table):
            return []

    options = {
        "table_primary_keys": [
            {
                "source_table": "orders_src",
                "target_table": "orders_tgt",
                "primary_keys": ["order_id", "line_id"],
                "target_primary_keys": ["id"],
            }
        ]
    }

    primary_keys, pk_mapping, error = service._resolve_primary_keys(
        source_conn=NoPkSourceConnector(),
        options=options,
        source_table="orders_src",
        target_table="orders_tgt",
    )

    assert primary_keys == []
    assert pk_mapping == {}
    assert error is not None
    assert "数量不一致" in error
