"""DMConnector 行为测试"""
from __future__ import annotations

import sys
import types

from app.core.connector.dm import DMConnector


class _FakeCursor:
    def __init__(self, connection):
        self._connection = connection
        self._sql = ""

    def execute(self, sql: str):
        self._sql = sql
        self._connection.executed_sql.append(sql)

    def fetchone(self):
        if "V$INSTANCE" in self._sql:
            return (self._connection.instance_name,)
        if "V$DM_INI" in self._sql:
            return (self._connection.instance_name,)
        if "V$VERSION" in self._sql:
            return (self._connection.version,)
        return None

    def close(self):
        return None


class _FakeConnection:
    def __init__(self, instance_name: str = "DM8", version: str = "DM Database Server 64 V8"):
        self.instance_name = instance_name
        self.version = version
        self.executed_sql = []
        self.closed = False

    def cursor(self):
        return _FakeCursor(self)

    def close(self):
        self.closed = True


def test_dm_test_connection_fails_when_database_name_not_match_instance(monkeypatch):
    fake_connection = _FakeConnection(instance_name="DM8")
    monkeypatch.setitem(
        sys.modules,
        "dmPython",
        types.SimpleNamespace(connect=lambda dsn: fake_connection),
    )

    connector = DMConnector(
        host="127.0.0.1",
        port=5236,
        database="NOT_EXISTS",
        username="SYSDBA",
        password="qa_pwd",
        schema="QA_SCHEMA",
    )
    result = connector.test_connection()

    assert result["success"] is False
    assert "实例名不匹配" in result["message"]
    assert "DM8" in result["message"]
    assert "NOT_EXISTS" in result["message"]
    assert fake_connection.closed is True


def test_dm_test_connection_accepts_case_insensitive_instance_name(monkeypatch):
    fake_connection = _FakeConnection(instance_name="DM8")
    monkeypatch.setitem(
        sys.modules,
        "dmPython",
        types.SimpleNamespace(connect=lambda dsn: fake_connection),
    )

    connector = DMConnector(
        host="127.0.0.1",
        port=5236,
        database="dm8",
        username="SYSDBA",
        password="qa_pwd",
        schema="QA_SCHEMA",
    )
    result = connector.test_connection()

    assert result["success"] is True
    assert result["version"] == "DM Database Server 64 V8"
    assert fake_connection.closed is True
