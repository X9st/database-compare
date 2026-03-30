"""TaskManager 并发槽位调度测试"""
from __future__ import annotations

import asyncio
import time

import pytest

from app.core.task.manager import TaskManager


@pytest.mark.asyncio
async def test_task_manager_run_slot_limits_concurrency():
    manager = TaskManager()
    starts = []
    ends = []

    async def worker(worker_id: int):
        slot_key = await manager.acquire_run_slot(1)
        starts.append((worker_id, time.monotonic()))
        try:
            await asyncio.sleep(0.05)
        finally:
            ends.append((worker_id, time.monotonic()))
            manager.release_run_slot(slot_key)

    await asyncio.gather(worker(1), worker(2))

    # 并发上限=1 时，第二个任务应在第一个结束后才进入临界区
    first_end = sorted(ends, key=lambda item: item[1])[0][1]
    second_start = sorted(starts, key=lambda item: item[1])[1][1]
    assert second_start >= first_end
