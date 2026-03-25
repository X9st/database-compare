"""DataSourceService 表检索测试"""
from __future__ import annotations

import uuid

from app.core.connector.base import TableInfo
from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.models.datasource import DataSource
from app.services.datasource_service import DataSourceService
from app.utils.crypto import encrypt


class StubConnector:
    def connect(self) -> bool:
        return True

    def disconnect(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def get_tables(self):
        return [
            TableInfo(name="users"),
            TableInfo(name="orders"),
            TableInfo(name="products"),
        ]


def test_get_tables_supports_keyword_filter(monkeypatch):
    init_database()
    db = SessionLocal()
    ds_id = str(uuid.uuid4())
    try:
        ds = DataSource(
            id=ds_id,
            name="qa-mysql",
            db_type="mysql",
            host="127.0.0.1",
            port=3306,
            database="qa_compare",
            schema=None,
            username="qa_user",
            password_encrypted=encrypt("qa_pwd"),
            charset="UTF-8",
            timeout=1,
        )
        db.add(ds)
        db.commit()

        monkeypatch.setattr(
            "app.services.datasource_service.ConnectorFactory.create",
            lambda **kwargs: StubConnector()
        )

        service = DataSourceService(db)
        all_tables = service.get_tables(ds_id)
        filtered_tables = service.get_tables(ds_id, keyword="us")

        assert [t.name for t in all_tables] == ["users", "orders", "products"]
        assert [t.name for t in filtered_tables] == ["users"]
    finally:
        db.query(DataSource).filter(DataSource.id == ds_id).delete()
        db.commit()
        db.close()
