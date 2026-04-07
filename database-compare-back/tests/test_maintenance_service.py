"""启动维护服务测试"""
from __future__ import annotations

import uuid
from datetime import datetime

from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.models.compare_task import CompareTask, CompareResult, StructureDiff, DataDiff
from app.models.datasource import DataSource
from app.models.settings import CompareTemplate
from app.services.maintenance_service import MaintenanceService
from app.utils.crypto import encrypt


def test_cleanup_legacy_datasources_cascades_related_data():
    init_database()
    db = SessionLocal()
    try:
        legacy_ds = DataSource(
            id=str(uuid.uuid4()),
            name="legacy-pg",
            db_type="postgresql",
            host="127.0.0.1",
            port=5432,
            database="qa",
            username="qa",
            password_encrypted=encrypt("pwd"),
            charset="UTF-8",
            timeout=30,
        )
        active_ds = DataSource(
            id=str(uuid.uuid4()),
            name="active-mysql",
            db_type="mysql",
            host="127.0.0.1",
            port=3306,
            database="qa",
            username="qa",
            password_encrypted=encrypt("pwd"),
            charset="UTF-8",
            timeout=30,
        )
        db.add_all([legacy_ds, active_ds])
        db.commit()
        legacy_id = legacy_ds.id

        task_id = str(uuid.uuid4())
        result_id = str(uuid.uuid4())
        db.add(
            CompareTask(
                id=task_id,
                source_id=legacy_ds.id,
                target_id=active_ds.id,
                status="completed",
                config={"source_id": legacy_ds.id, "target_id": active_ds.id, "table_selection": {"mode": "all", "tables": []}, "options": {"mode": "full"}},
                progress={},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
        )
        db.add(CompareResult(id=result_id, task_id=task_id, summary={}))
        db.add(
            StructureDiff(
                id=str(uuid.uuid4()),
                result_id=result_id,
                table_name="users",
                diff_type="column_missing",
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
            )
        )
        db.add(
            CompareTemplate(
                id=str(uuid.uuid4()),
                name="legacy-template",
                description="legacy",
                config={"source_id": legacy_ds.id, "target_id": active_ds.id},
            )
        )
        db.commit()

        stats = MaintenanceService(db).cleanup_legacy_datasources()
        assert stats["datasources_deleted"] == 1
        assert stats["tasks_deleted"] == 1
        assert stats["results_deleted"] == 1
        assert stats["templates_deleted"] == 1

        assert db.query(DataSource).filter(DataSource.id == legacy_id).count() == 0
        assert db.query(CompareTask).filter(CompareTask.id == task_id).count() == 0
        assert db.query(CompareResult).filter(CompareResult.id == result_id).count() == 0
    finally:
        db.query(CompareTask).delete()
        db.query(CompareResult).delete()
        db.query(StructureDiff).delete()
        db.query(DataDiff).delete()
        db.query(CompareTemplate).delete()
        db.query(DataSource).delete()
        db.commit()
        db.close()


def test_recover_stale_running_tasks_marks_unfinished_as_failed():
    init_database()
    db = SessionLocal()
    try:
        source_ds = DataSource(
            id=str(uuid.uuid4()),
            name="src-mysql",
            db_type="mysql",
            host="127.0.0.1",
            port=3306,
            database="qa",
            username="qa",
            password_encrypted=encrypt("pwd"),
            charset="UTF-8",
            timeout=30,
        )
        target_ds = DataSource(
            id=str(uuid.uuid4()),
            name="tgt-inceptor",
            db_type="inceptor",
            host="127.0.0.1",
            port=10000,
            database="default",
            username="admin",
            password_encrypted=encrypt("pwd"),
            charset="UTF-8",
            timeout=30,
        )
        db.add_all([source_ds, target_ds])
        db.commit()

        statuses = ["pending", "running", "paused", "completed", "failed", "cancelled"]
        task_ids = {}
        for status in statuses:
            task_id = str(uuid.uuid4())
            task_ids[status] = task_id
            db.add(
                CompareTask(
                    id=task_id,
                    source_id=source_ds.id,
                    target_id=target_ds.id,
                    status=status,
                    config={
                        "source_id": source_ds.id,
                        "target_id": target_ds.id,
                        "table_selection": {"mode": "all", "tables": []},
                        "options": {"mode": "full"},
                    },
                    progress={},
                    started_at=datetime.utcnow(),
                )
            )
        db.commit()

        recovered = MaintenanceService(db).recover_stale_running_tasks()
        assert recovered == 3

        for status in ["pending", "running", "paused"]:
            task = db.query(CompareTask).filter(CompareTask.id == task_ids[status]).first()
            assert task is not None
            assert task.status == "failed"
            assert task.completed_at is not None
            assert task.error_message

        for status in ["completed", "failed", "cancelled"]:
            task = db.query(CompareTask).filter(CompareTask.id == task_ids[status]).first()
            assert task is not None
            assert task.status == status
    finally:
        db.query(CompareTask).delete()
        db.query(CompareResult).delete()
        db.query(StructureDiff).delete()
        db.query(DataDiff).delete()
        db.query(CompareTemplate).delete()
        db.query(DataSource).delete()
        db.commit()
        db.close()
