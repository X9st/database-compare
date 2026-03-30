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


def test_datasource_file_upload_endpoint_accepts_excel():
    client = _build_client()
    resp = client.post(
        "/api/v1/datasources/files/upload",
        files={"file": ("report.xlsx", b"fake-excel-content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()["data"]
    assert payload["original_name"] == "report.xlsx"
    assert payload["file_type"] == "xlsx"
    assert payload["storage_key"].endswith(".xlsx")


def test_create_remote_dataset_endpoint(monkeypatch):
    client = _build_client()

    def _fake_create_remote_dataset(self, _request):
        now = datetime.utcnow().isoformat()
        return {
            "id": "remote-ds-1",
            "name": "remote-dataset",
            "group_id": None,
            "group_name": None,
            "db_type": "dbf",
            "host": "local-file",
            "port": 0,
            "database": "dataset",
            "schema": None,
            "username": "file_user",
            "charset": "UTF-8",
            "timeout": 30,
            "extra_config": {
                "mode": "remote_dataset",
                "sftp": {"host": "10.0.0.1", "port": 22, "username": "user", "base_dir": "/inbound"},
                "snapshot": {
                    "dataset_root": "data/uploads/datasets/remote-ds-1/snapshot_x",
                    "table_index": {"orders": {"storage_key": "/tmp/orders.dbf", "file_type": "dbf"}},
                    "file_count": 1,
                    "table_count": 1,
                    "failed_files": [],
                    "last_refresh_at": now,
                },
            },
            "created_at": now,
            "updated_at": now,
        }

    monkeypatch.setattr(
        "app.services.datasource_service.DataSourceService.create_remote_dataset",
        _fake_create_remote_dataset,
    )

    resp = client.post(
        "/api/v1/datasources/remote-datasets",
        json={
            "name": "remote-dataset",
            "db_type": "dbf",
            "extra_config": {
                "mode": "remote_dataset",
                "file_type": "dbf",
                "sftp": {
                    "host": "10.0.0.1",
                    "port": 22,
                    "username": "user",
                    "password": "pwd",
                    "base_dir": "/inbound",
                },
            },
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["extra_config"]["mode"] == "remote_dataset"


def test_refresh_remote_dataset_endpoint(monkeypatch):
    client = _build_client()

    def _fake_refresh(self, ds_id: str):
        return {
            "datasource_id": ds_id,
            "file_count": 2,
            "table_count": 3,
            "failed_files": [{"file_name": "bad.dbf", "error": "decode failed"}],
            "last_refresh_at": datetime.utcnow().isoformat(),
        }

    monkeypatch.setattr(
        "app.services.datasource_service.DataSourceService.refresh_remote_dataset",
        _fake_refresh,
    )

    resp = client.post("/api/v1/datasources/any-id/refresh")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["file_count"] == 2
    assert len(data["failed_files"]) == 1


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


def test_history_keyword_matches_task_and_datasource_names():
    client = _build_client()
    source_name = f"qa-history-src-{uuid.uuid4().hex[:6]}"
    target_name = f"qa-history-tgt-{uuid.uuid4().hex[:6]}"
    source_id = _create_datasource_record(source_name)
    target_id = _create_datasource_record(target_name)
    task_id = str(uuid.uuid4())

    db = SessionLocal()
    try:
        db.add(
            CompareTask(
                id=task_id,
                source_id=source_id,
                target_id=target_id,
                status="completed",
                config={
                    "source_id": source_id,
                    "target_id": target_id,
                    "table_selection": {"mode": "all", "tables": []},
                    "options": {"mode": "full"},
                },
                progress={"completed_source_tables": []},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
        )
        db.commit()
    finally:
        db.close()

    try:
        by_task_resp = client.get("/api/v1/history", params={"keyword": task_id})
        assert by_task_resp.status_code == 200, by_task_resp.text
        assert any(item["task_id"] == task_id for item in by_task_resp.json()["data"])

        by_source_resp = client.get("/api/v1/history", params={"keyword": source_name})
        assert by_source_resp.status_code == 200, by_source_resp.text
        assert any(item["task_id"] == task_id for item in by_source_resp.json()["data"])

        by_target_resp = client.get("/api/v1/history", params={"keyword": target_name})
        assert by_target_resp.status_code == 200, by_target_resp.text
        assert any(item["task_id"] == task_id for item in by_target_resp.json()["data"])
    finally:
        db = SessionLocal()
        try:
            db.query(CompareTask).filter(CompareTask.id == task_id).delete()
            db.commit()
        finally:
            db.close()
        _delete_datasource_records(source_id, target_id)


def test_result_table_detail_returns_real_row_counts_and_compare_time():
    client = _build_client()
    source_id = _create_datasource_record(f"qa-src-{uuid.uuid4().hex[:8]}")
    target_id = _create_datasource_record(f"qa-tgt-{uuid.uuid4().hex[:8]}")
    task_id = str(uuid.uuid4())
    result_id = str(uuid.uuid4())
    table_name = "users -> users_bak"

    db = SessionLocal()
    try:
        db.add(
            CompareTask(
                id=task_id,
                source_id=source_id,
                target_id=target_id,
                status="completed",
                config={
                    "source_id": source_id,
                    "target_id": target_id,
                    "table_selection": {"mode": "mapping", "tables": []},
                    "options": {"mode": "full"},
                },
                progress={
                    "completed_source_tables": ["users"],
                    "table_stats": {
                        table_name: {
                            "source_table": "users",
                            "target_table": "users_bak",
                            "source_row_count": 123,
                            "target_row_count": 125,
                            "compare_time_ms": 987,
                            "structure_diffs_count": 1,
                            "data_diffs_count": 2,
                        }
                    },
                },
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
        )
        db.add(
            CompareResult(
                id=result_id,
                task_id=task_id,
                summary={
                    "total_tables": 1,
                    "structure_match_tables": 0,
                    "structure_diff_tables": 1,
                    "data_match_tables": 0,
                    "data_diff_tables": 1,
                    "no_diff_tables": 0,
                    "total_structure_diffs": 1,
                    "total_data_diffs": 2,
                    "structure_diff_type_counts": {"column_missing": 1},
                    "data_diff_type_counts": {"value_diff": 2},
                },
            )
        )
        db.add(
            StructureDiff(
                id=str(uuid.uuid4()),
                result_id=result_id,
                table_name=table_name,
                diff_type="column_missing",
                field_name="email",
                diff_detail="目标库缺少字段",
            )
        )
        db.add(
            DataDiff(
                id=str(uuid.uuid4()),
                result_id=result_id,
                table_name=table_name,
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

    try:
        detail_resp = client.get(f"/api/v1/compare/results/{result_id}/tables/{table_name}")
        assert detail_resp.status_code == 200, detail_resp.text
        detail = detail_resp.json()["data"]
        assert detail["source_row_count"] == 123
        assert detail["target_row_count"] == 125
        assert detail["compare_time_ms"] == 987

        summary_resp = client.get(f"/api/v1/compare/results/{result_id}")
        assert summary_resp.status_code == 200, summary_resp.text
        summary = summary_resp.json()["data"]["summary"]
        assert summary["no_diff_tables"] == 0
        assert summary["structure_diff_type_counts"]["column_missing"] == 1
        assert summary["data_diff_type_counts"]["value_diff"] == 2
    finally:
        db = SessionLocal()
        try:
            db.query(StructureDiff).filter(StructureDiff.result_id == result_id).delete()
            db.query(DataDiff).filter(DataDiff.result_id == result_id).delete()
            db.query(CompareResult).filter(CompareResult.id == result_id).delete()
            db.query(CompareTask).filter(CompareTask.id == task_id).delete()
            db.commit()
        finally:
            db.close()
        _delete_datasource_records(source_id, target_id)


def test_result_compare_endpoint_returns_added_resolved_and_unchanged():
    client = _build_client()
    source_id = _create_datasource_record(f"qa-src-{uuid.uuid4().hex[:8]}")
    target_id = _create_datasource_record(f"qa-tgt-{uuid.uuid4().hex[:8]}")
    baseline_task_id = str(uuid.uuid4())
    current_task_id = str(uuid.uuid4())
    baseline_result_id = str(uuid.uuid4())
    current_result_id = str(uuid.uuid4())

    db = SessionLocal()
    try:
        db.add_all([
            CompareTask(
                id=baseline_task_id,
                source_id=source_id,
                target_id=target_id,
                status="completed",
                config={"source_id": source_id, "target_id": target_id, "table_selection": {"mode": "all", "tables": []}, "options": {"mode": "full"}},
            ),
            CompareTask(
                id=current_task_id,
                source_id=source_id,
                target_id=target_id,
                status="completed",
                config={"source_id": source_id, "target_id": target_id, "table_selection": {"mode": "all", "tables": []}, "options": {"mode": "full"}},
            ),
            CompareResult(id=baseline_result_id, task_id=baseline_task_id, summary={"total_tables": 1}),
            CompareResult(id=current_result_id, task_id=current_task_id, summary={"total_tables": 1}),
        ])

        # baseline: A(struct) + B(data)
        struct_a_id = str(uuid.uuid4())
        data_b_id = str(uuid.uuid4())
        db.add(
            StructureDiff(
                id=struct_a_id,
                result_id=baseline_result_id,
                table_name="users",
                diff_type="column_missing",
                field_name="email",
                diff_detail="missing email",
            )
        )
        db.add(
            DataDiff(
                id=data_b_id,
                result_id=baseline_result_id,
                table_name="users",
                primary_key={"id": 1},
                diff_type="value_diff",
                diff_columns=["name"],
                source_values={"name": "Alice"},
                target_values={"name": "Alicia"},
            )
        )

        # current: A(struct, unchanged) + C(data, added)
        db.add(
            StructureDiff(
                id=str(uuid.uuid4()),
                result_id=current_result_id,
                table_name="users",
                diff_type="column_missing",
                field_name="email",
                diff_detail="missing email",
            )
        )
        db.add(
            DataDiff(
                id=str(uuid.uuid4()),
                result_id=current_result_id,
                table_name="users",
                primary_key={"id": 2},
                diff_type="row_extra_in_target",
                diff_columns=[],
                source_values={},
                target_values={"id": 2},
            )
        )
        db.commit()
    finally:
        db.close()

    try:
        resp = client.post(
            "/api/v1/compare/results/compare",
            json={
                "baseline_result_id": baseline_result_id,
                "current_result_id": current_result_id,
            },
        )
        assert resp.status_code == 200, resp.text
        payload = resp.json()["data"]
        summary = payload["summary"]
        assert summary["added"] == 1
        assert summary["resolved"] == 1
        assert summary["unchanged"] == 1
        assert summary["added_data"] == 1
        assert summary["resolved_data"] == 1
        assert summary["unchanged_structure"] == 1

        export_resp = client.post(
            "/api/v1/compare/results/compare/export",
            json={
                "baseline_result_id": baseline_result_id,
                "current_result_id": current_result_id,
                "format": "txt",
            },
        )
        assert export_resp.status_code == 200, export_resp.text
        export_data = export_resp.json()["data"]
        assert export_data["file_name"].endswith(".txt")
        download_resp = client.get(export_data["download_url"])
        assert download_resp.status_code == 200
        assert len(download_resp.content) > 0
    finally:
        db = SessionLocal()
        try:
            db.query(StructureDiff).filter(StructureDiff.result_id.in_([baseline_result_id, current_result_id])).delete(synchronize_session=False)
            db.query(DataDiff).filter(DataDiff.result_id.in_([baseline_result_id, current_result_id])).delete(synchronize_session=False)
            db.query(CompareResult).filter(CompareResult.id.in_([baseline_result_id, current_result_id])).delete(synchronize_session=False)
            db.query(CompareTask).filter(CompareTask.id.in_([baseline_task_id, current_task_id])).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()
        _delete_datasource_records(source_id, target_id)
