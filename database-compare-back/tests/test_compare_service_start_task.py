"""CompareService.start_task 非阻塞调度测试"""
from __future__ import annotations

import pytest

from app.services.compare_service import CompareService


class _DummyTask:
    def __init__(self, status: str = "pending"):
        self.status = status
        self.started_at = None


class _DummyQuery:
    def __init__(self, task: _DummyTask | None):
        self._task = task

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._task


class _DummyDb:
    def __init__(self, task: _DummyTask | None):
        self._task = task
        self.commit_count = 0

    def query(self, *_args, **_kwargs):
        return _DummyQuery(self._task)

    def commit(self):
        self.commit_count += 1


class _DummyLoop:
    def __init__(self):
        self.calls = []

    def run_in_executor(self, executor, func, *args):
        self.calls.append((executor, func, args))
        return None


@pytest.mark.asyncio
async def test_start_task_dispatches_worker_and_returns_quickly(monkeypatch):
    task = _DummyTask(status="pending")
    db = _DummyDb(task=task)
    service = CompareService(db=db)

    dummy_loop = _DummyLoop()
    monkeypatch.setattr("app.services.compare_service.asyncio.get_running_loop", lambda: dummy_loop)

    payload = await service.start_task("task-001")

    assert payload["task_id"] == "task-001"
    assert payload["status"] == "running"
    assert task.status == "running"
    assert task.started_at is not None
    assert db.commit_count == 1
    assert len(dummy_loop.calls) == 1
    _, func, args = dummy_loop.calls[0]
    assert func == service._execute_compare_in_worker
    assert args == ("task-001",)
