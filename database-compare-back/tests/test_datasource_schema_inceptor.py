"""DataSource schema tests for Inceptor auth modes."""
from __future__ import annotations

from app.schemas.datasource import CreateDataSourceRequest, TestConnectionRequest as DataSourceTestConnectionRequest


def test_create_datasource_inceptor_allows_empty_password_with_none_auth():
    req = CreateDataSourceRequest(
        name="inceptor-none",
        db_type="inceptor",
        host="127.0.0.1",
        port=10000,
        database="default",
        username="admin",
        password=None,
        extra_config={"inceptor_auth_mode": "NONE"},
    )
    assert req.db_type == "inceptor"


def test_test_connection_inceptor_allows_empty_password_with_nosasl_auth():
    req = DataSourceTestConnectionRequest(
        db_type="inceptor",
        host="127.0.0.1",
        port=10000,
        database="default",
        username="admin",
        password=None,
        extra_config={"auth_mode": "NOSASL"},
    )
    assert req.db_type == "inceptor"
