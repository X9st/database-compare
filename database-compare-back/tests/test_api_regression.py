"""关键接口回归测试"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import uuid

from fastapi.testclient import TestClient

from app.application import create_app
from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.models.compare_task import CompareTask, CompareResult, StructureDiff, DataDiff
from app.models.datasource import DataSource
from app.models.settings import CompareTemplate
from app.utils.crypto import encrypt


def _build_client() -> TestClient:
    init_database()
    return TestClient(create_app())


def _create_datasource_record(name: str, db_type: str = "mysql") -> str:
    db = SessionLocal()
    try:
        ds = DataSource(
            id=str(uuid.uuid4()),
            name=name,
            db_type=db_type,
            host="127.0.0.1",
            port=3306 if db_type == "mysql" else 5432,
            database="qa_compare",
            schema=None,
            username="qa_user",
            password_encrypted=encrypt("qa_pwd"),
            charset="UTF-8",
            timeout=1,
        )
        db.add(ds)
        db.commit()
        return ds.id
    finally:
        db.close()


def _delete_datasource_records(*ids: str) -> None:
    db = SessionLocal()
    try:
        for ds_id in ids:
            if ds_id:
                ds = db.query(DataSource).filter(DataSource.id == ds_id).first()
                if ds:
                    db.delete(ds)
        db.commit()
    finally:
        db.close()


def test_compare_start_returns_snake_case_task_id():
    client = _build_client()
    source_id = _create_datasource_record(f"qa-src-{uuid.uuid4().hex[:8]}")
    target_id = _create_datasource_record(f"qa-tgt-{uuid.uuid4().hex[:8]}")

    try:
        resp = client.post(
            "/api/v1/compare/start",
            json={
                "source_id": source_id,
                "target_id": target_id,
                "table_selection": {"mode": "all", "tables": []},
                "options": {
                    "mode": "full",
                    "structure_options": {
                        "compare_index": True,
                        "compare_constraint": True,
                        "compare_comment": True,
                    },
                    "data_options": {
                        "float_precision": 6,
                        "ignore_case": False,
                        "trim_whitespace": True,
                        "datetime_precision": "second",
                        "skip_large_fields": True,
                        "page_size": 1000,
                    },
                },
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "task_id" in data
        assert "taskId" not in data
    finally:
        _delete_datasource_records(source_id, target_id)


def test_settings_export_import_roundtrip():
    client = _build_client()

    export_resp = client.post(
        "/api/v1/settings/export",
        json={
            "include_datasources": True,
            "include_templates": True,
            "include_rules": True,
            "include_system_settings": True,
        },
    )
    assert export_resp.status_code == 200, export_resp.text
    export_data = export_resp.json()["data"]
    assert export_data["file_name"].endswith(".json")
    assert export_data["download_url"].startswith("/api/v1/files/download/")

    download_resp = client.get(export_data["download_url"])
    assert download_resp.status_code == 200

    import_resp = client.post(
        "/api/v1/settings/import",
        files={
            "config_file": (
                export_data["file_name"],
                download_resp.content,
                "application/json",
            )
        },
    )
    assert import_resp.status_code == 200, import_resp.text
    import_data = import_resp.json()["data"]
    assert "datasources_imported" in import_data
    assert "templates_imported" in import_data
    assert "rules_imported" in import_data
    assert "system_settings_imported" in import_data


def test_template_create_task_and_result_export_download():
    client = _build_client()
    source_id = _create_datasource_record(f"qa-src-{uuid.uuid4().hex[:8]}")
    target_id = _create_datasource_record(f"qa-tgt-{uuid.uuid4().hex[:8]}")

    template_id = None
    task_id = None
    result_id = None

    try:
        template_resp = client.post(
            "/api/v1/settings/templates",
            json={
                "name": f"qa-template-{uuid.uuid4().hex[:8]}",
                "description": "qa regression template",
                "config": {
                    "source_id": source_id,
                    "target_id": target_id,
                    "table_selection": {"mode": "all", "tables": []},
                    "options": {
                        "mode": "full",
                        "structure_options": {
                            "compare_index": True,
                            "compare_constraint": True,
                            "compare_comment": True,
                        },
                        "data_options": {
                            "float_precision": 6,
                            "ignore_case": False,
                            "trim_whitespace": True,
                            "datetime_precision": "second",
                            "skip_large_fields": True,
                            "page_size": 1000,
                        },
                    },
                },
            },
        )
        assert template_resp.status_code == 200, template_resp.text
        template_id = template_resp.json()["data"]["id"]

        create_task_resp = client.post(
            f"/api/v1/settings/templates/{template_id}/create-task",
            json={"override": {}},
        )
        assert create_task_resp.status_code == 200, create_task_resp.text
        create_task_data = create_task_resp.json()["data"]
        assert create_task_data["status"] == "pending"
        task_id = create_task_data["task_id"]

        db = SessionLocal()
        try:
            task = db.query(CompareTask).filter(CompareTask.id == task_id).first()
            task.status = "completed"
            task.started_at = datetime.utcnow()
            task.completed_at = datetime.utcnow()

            result_id = str(uuid.uuid4())
            result = CompareResult(
                id=result_id,
                task_id=task_id,
                summary={
                    "total_tables": 1,
                    "structure_match_tables": 0,
                    "structure_diff_tables": 1,
                    "data_match_tables": 1,
                    "data_diff_tables": 0,
                    "total_structure_diffs": 1,
                    "total_data_diffs": 0,
                },
            )
            db.add(result)
            db.add(
                StructureDiff(
                    id=str(uuid.uuid4()),
                    result_id=result_id,
                    table_name="users",
                    diff_type="column_missing",
                    field_name="email",
                    source_value="varchar(255)",
                    target_value=None,
                    diff_detail="目标库字段缺失",
                )
            )
            db.add(
                DataDiff(
                    id=str(uuid.uuid4()),
                    result_id=result_id,
                    table_name="users",
                    primary_key={"id": 1},
                    diff_type="value_diff",
                    diff_columns=["name"],
                    source_values={"name": "Alice"},
                    target_values={"name": "Alicia"},
                )
            )
            db.commit()
        finally:
            db.close()

        export_resp = client.post(
            f"/api/v1/compare/results/{result_id}/export",
            json={
                "format": "txt",
                "options": {
                    "include_structure_diffs": True,
                    "include_data_diffs": True,
                    "max_data_diffs": 100,
                },
            },
        )
        assert export_resp.status_code == 200, export_resp.text
        export_data = export_resp.json()["data"]
        assert export_data["file_name"].endswith(".txt")

        file_resp = client.get(export_data["download_url"])
        assert file_resp.status_code == 200
        assert len(file_resp.content) > 0

        file_path = Path(export_data["file_path"])
        assert file_path.exists()
    finally:
        db = SessionLocal()
        try:
            if result_id:
                db.query(StructureDiff).filter(StructureDiff.result_id == result_id).delete()
                db.query(DataDiff).filter(DataDiff.result_id == result_id).delete()
                db.query(CompareResult).filter(CompareResult.id == result_id).delete()
            if task_id:
                db.query(CompareTask).filter(CompareTask.id == task_id).delete()
            if template_id:
                db.query(CompareTemplate).filter(CompareTemplate.id == template_id).delete()
            db.commit()
        finally:
            db.close()

        _delete_datasource_records(source_id, target_id)
