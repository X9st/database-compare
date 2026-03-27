"""InceptorConnector 离线行为测试"""
from __future__ import annotations

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
