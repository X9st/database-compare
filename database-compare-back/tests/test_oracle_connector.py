"""OracleConnector 回归测试"""
from __future__ import annotations

import sys
import types

from app.core.connector.oracle import OracleConnector


class _FakeConnection:
    def close(self):
        return None


def test_oracle_connect_does_not_pass_legacy_encoding_kw(monkeypatch):
    captured = {}

    def fake_makedsn(host, port, service_name):
        return f"{host}:{port}/{service_name}"

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return _FakeConnection()

    fake_module = types.SimpleNamespace(makedsn=fake_makedsn, connect=fake_connect)
    monkeypatch.setitem(sys.modules, "oracledb", fake_module)

    connector = OracleConnector(
        host="127.0.0.1",
        port=1521,
        database="FREEPDB1",
        username="qa_user",
        password="qa_pwd",
    )
    assert connector.connect() is True
    assert captured["dsn"] == "127.0.0.1:1521/FREEPDB1"
    assert "encoding" not in captured
