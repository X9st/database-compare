"""DataSourceService 表检索测试"""
from __future__ import annotations

import uuid
from pathlib import Path

from app.core.connector.base import TableInfo, ColumnInfo, IndexInfo, ConstraintInfo
from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.models.datasource import DataSource
from app.services.datasource_service import DataSourceService
from app.utils.crypto import encrypt
from app.schemas.datasource import CreateDataSourceRequest


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
            TableInfo(name="users", comment="用户表"),
            TableInfo(name="orders"),
            TableInfo(name="products"),
        ]

    def get_columns(self, table_name: str):
        return [
            ColumnInfo(name="id", data_type="int", is_primary_key=True),
            ColumnInfo(name="name", data_type="varchar", length=100),
        ]

    def get_indexes(self, table_name: str):
        return [
            IndexInfo(
                name="pk_users",
                columns=["id"],
                is_unique=True,
                is_primary=True,
                index_type="BTREE",
            )
        ]

    def get_constraints(self, table_name: str):
        return [
            ConstraintInfo(
                name="pk_users",
                constraint_type="PRIMARY KEY",
                columns=["id"],
            )
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


def test_get_table_schema_returns_table_comment(monkeypatch):
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
        schema = service.get_table_schema(ds_id, "users")

        assert schema is not None
        assert schema.table_name == "users"
        assert schema.comment == "用户表"
        assert len(schema.columns) == 2
    finally:
        db.query(DataSource).filter(DataSource.id == ds_id).delete()
        db.commit()
        db.close()


def test_create_file_datasource_with_uploaded_metadata(tmp_path: Path):
    init_database()
    db = SessionLocal()
    created_id = None
    try:
        service = DataSourceService(db)
        service.upload_dir = tmp_path
        uploaded = service.upload_datasource_file("sales.xlsx", b"fake-xlsx-content")

        request = CreateDataSourceRequest(
            name="qa-excel",
            db_type="excel",
            database="sales",
            extra_config={
                "storage_key": uploaded.storage_key,
                "original_name": uploaded.original_name,
                "file_type": uploaded.file_type,
                "file_id": uploaded.file_id,
            },
        )
        created = service.create(request)
        created_id = created.id

        assert created.db_type == "excel"
        assert created.extra_config is not None
        assert created.extra_config.get("storage_key") == uploaded.storage_key
    finally:
        if created_id:
            db.query(DataSource).filter(DataSource.id == created_id).delete()
            db.commit()
        db.close()
