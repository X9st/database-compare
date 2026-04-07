"""InceptorConnector 离线行为测试"""
from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from app.core.connector.inceptor import InceptorConnector


class StubCursor:
    def __init__(self):
        self.executed_sql = []
        self._rows = []
        self.description = [("id",)]

    def execute(self, sql: str):
        self.executed_sql.append(sql)

        if sql.startswith("SHOW CREATE TABLE"):
            self._rows = [
                ("CREATE TABLE db.t_user (",),
                ("  `id` BIGINT,",),
                ("  `tenant_id` STRING,",),
                ("  CONSTRAINT pk_t_user PRIMARY KEY (`id`, `tenant_id`) DISABLE NOVALIDATE",),
                (")",),
            ]
            return

        if "LIMIT 2, 2" in sql:
            raise RuntimeError("offset syntax not supported")

        if sql.endswith("LIMIT 4"):
            self._rows = [(1,), (2,), (3,), (4,)]
            return

        if sql.endswith("LIMIT 2"):
            self._rows = [(1,), (2,)]
            return

        self._rows = []

    def fetchall(self):
        return list(self._rows)


class _DummyCursor:
    def close(self):
        return None


class _DummyConnection:
    def cursor(self):
        return _DummyCursor()

    def close(self):
        return None


class _BrokenCursor:
    def close(self):
        raise RuntimeError("close failed")


class _BrokenConnection:
    def close(self):
        raise RuntimeError("close failed")


class _TimeoutSocket:
    def __init__(self):
        self.last_timeout = None

    def setTimeout(self, value):
        self.last_timeout = value


class _TimeoutTransport:
    def __init__(self, sock):
        self._trans = sock


class _TimeoutConnection:
    def __init__(self, sock):
        self._transport = _TimeoutTransport(sock)

    def cursor(self):
        return _DummyCursor()

    def close(self):
        return None


def _build_connector(cursor: StubCursor) -> InceptorConnector:
    conn = InceptorConnector(
        host="127.0.0.1",
        port=10000,
        database="default",
        username="u",
        password="p",
    )
    conn._cursor = cursor
    return conn


def test_get_primary_keys_parses_show_create_table():
    conn = _build_connector(StubCursor())
    assert conn.get_primary_keys("t_user") == ["id", "tenant_id"]


def test_fetch_data_offset_falls_back_to_limit_plus_slice():
    cursor = StubCursor()
    conn = _build_connector(cursor)

    rows = conn.fetch_data("t_user", columns=["id"], offset=2, limit=2)

    assert rows == [{"id": 3}, {"id": 4}]
    assert any("LIMIT 2, 2" in sql for sql in cursor.executed_sql)
    assert any(sql.endswith("LIMIT 4") for sql in cursor.executed_sql)


def test_connect_fallbacks_to_nosasl_when_ldap_failed(monkeypatch):
    attempts = []

    def _fake_connect(**kwargs):
        attempts.append(kwargs)
        if kwargs.get("auth") == "LDAP":
            raise RuntimeError("TSocket read 0 bytes")
        if kwargs.get("auth") == "NOSASL":
            return _DummyConnection()
        raise RuntimeError(f"unexpected mode: {kwargs.get('auth')}")

    fake_pyhive = SimpleNamespace(hive=SimpleNamespace(connect=_fake_connect))
    monkeypatch.setitem(sys.modules, "pyhive", fake_pyhive)

    conn = InceptorConnector(
        host="39.105.124.246",
        port=10000,
        database="default",
        username="admin",
        password="AAAaaa11",
    )
    assert conn.connect() is True

    assert [item.get("auth") for item in attempts[:2]] == ["LDAP", "NOSASL"]
    assert "password" in attempts[0]
    assert "password" not in attempts[1]


def test_connect_respects_explicit_auth_mode(monkeypatch):
    attempts = []

    def _fake_connect(**kwargs):
        attempts.append(kwargs)
        if kwargs.get("auth") == "NONE":
            return _DummyConnection()
        raise RuntimeError("should not be called")

    fake_pyhive = SimpleNamespace(hive=SimpleNamespace(connect=_fake_connect))
    monkeypatch.setitem(sys.modules, "pyhive", fake_pyhive)

    conn = InceptorConnector(
        host="39.105.124.246",
        port=10000,
        database="default",
        username="admin",
        password="AAAaaa11",
        extra_config={"inceptor_auth_mode": "NONE"},
    )
    assert conn.connect() is True
    assert [item.get("auth") for item in attempts] == ["NONE"]
    assert "password" not in attempts[0]


def test_connect_explicit_auth_mode_without_fallback_is_strict(monkeypatch):
    attempts = []

    def _fake_connect(**kwargs):
        attempts.append(kwargs)
        raise RuntimeError("invalid credentials")

    fake_pyhive = SimpleNamespace(hive=SimpleNamespace(connect=_fake_connect))
    monkeypatch.setitem(sys.modules, "pyhive", fake_pyhive)

    conn = InceptorConnector(
        host="39.105.124.246",
        port=10000,
        database="default",
        username="admin1",
        password="wrong",
        extra_config={"inceptor_auth_mode": "LDAP", "inceptor_transport_mode": "BINARY"},
    )

    with pytest.raises(ConnectionError):
        conn.connect()

    assert [item.get("auth") for item in attempts] == ["LDAP"]


def test_connect_error_message_contains_tsocket_guidance(monkeypatch):
    def _fake_connect(**_kwargs):
        raise RuntimeError("TSocket read 0 bytes")

    fake_pyhive = SimpleNamespace(hive=SimpleNamespace(connect=_fake_connect))
    monkeypatch.setitem(sys.modules, "pyhive", fake_pyhive)

    conn = InceptorConnector(
        host="39.105.124.246",
        port=10000,
        database="default",
        username="admin",
        password="AAAaaa11",
    )

    with pytest.raises(ConnectionError) as exc:
        conn.connect()

    message = str(exc.value)
    assert "TSocket read 0 bytes" in message
    assert "SSH 隧道" in message
    assert "认证模式" in message
    assert "传输模式" in message


def test_connect_fallbacks_to_http_basic_when_binary_fails(monkeypatch):
    attempts = []

    def _fake_connect(**kwargs):
        attempts.append(kwargs)
        if kwargs.get("scheme") == "http" and kwargs.get("auth") == "BASIC":
            return _DummyConnection()
        raise RuntimeError("TSocket read 0 bytes")

    fake_pyhive = SimpleNamespace(hive=SimpleNamespace(connect=_fake_connect))
    monkeypatch.setitem(sys.modules, "pyhive", fake_pyhive)

    conn = InceptorConnector(
        host="39.105.124.246",
        port=10000,
        database="default",
        username="admin",
        password="AAAaaa11",
    )
    assert conn.connect() is True

    assert any(item.get("scheme") is None and item.get("auth") == "LDAP" for item in attempts)
    assert any(item.get("scheme") == "http" and item.get("auth") == "BASIC" for item in attempts)


def test_connect_explicit_transport_mode_without_fallback_is_strict(monkeypatch):
    attempts = []

    def _fake_connect(**kwargs):
        attempts.append(kwargs)
        raise RuntimeError("TSocket read 0 bytes")

    fake_pyhive = SimpleNamespace(hive=SimpleNamespace(connect=_fake_connect))
    monkeypatch.setitem(sys.modules, "pyhive", fake_pyhive)

    conn = InceptorConnector(
        host="39.105.124.246",
        port=10000,
        database="default",
        username="admin",
        password="AAAaaa11",
        extra_config={"inceptor_transport_mode": "BINARY", "inceptor_auth_mode": "LDAP"},
    )
    with pytest.raises(ConnectionError):
        conn.connect()

    assert all(item.get("scheme") is None for item in attempts)


def test_disconnect_ignores_close_errors():
    conn = InceptorConnector(
        host="127.0.0.1",
        port=10000,
        database="default",
        username="admin",
        password="pwd",
    )
    conn._cursor = _BrokenCursor()
    conn._connection = _BrokenConnection()

    conn.disconnect()
    assert conn._cursor is None
    assert conn._connection is None


def test_connect_applies_socket_timeout(monkeypatch):
    sock = _TimeoutSocket()

    def _fake_connect(**_kwargs):
        return _TimeoutConnection(sock)

    fake_pyhive = SimpleNamespace(hive=SimpleNamespace(connect=_fake_connect))
    monkeypatch.setitem(sys.modules, "pyhive", fake_pyhive)

    conn = InceptorConnector(
        host="127.0.0.1",
        port=10000,
        database="default",
        username="admin",
        password="pwd",
        timeout=7,
        extra_config={"inceptor_auth_mode": "LDAP", "inceptor_transport_mode": "BINARY"},
    )
    assert conn.connect() is True
    assert sock.last_timeout == 7000
