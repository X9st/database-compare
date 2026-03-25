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
