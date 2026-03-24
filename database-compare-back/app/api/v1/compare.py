"""比对任务API"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.compare_service import CompareService
from app.schemas.compare import CreateTaskRequest
from app.schemas.common import Response

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> CompareService:
    return CompareService(db)


@router.post("/tasks")
async def create_task(
    request: CreateTaskRequest,
    service: CompareService = Depends(get_service)
):
    """创建比对任务"""
    try:
        data = service.create_task(request)
        return Response(message="任务创建成功", data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: str,
    service: CompareService = Depends(get_service)
):
    """启动比对任务"""
    try:
        data = await service.start_task(task_id)
        return Response(message="任务已启动", data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/pause")
async def pause_task(
    task_id: str,
    service: CompareService = Depends(get_service)
):
    """暂停比对任务"""
    if not service.pause_task(task_id):
        raise HTTPException(status_code=404, detail="任务不存在或无法暂停")
    return Response(message="任务已暂停", data={"task_id": task_id, "status": "paused"})


@router.post("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    service: CompareService = Depends(get_service)
):
    """恢复比对任务"""
    if not service.resume_task(task_id):
        raise HTTPException(status_code=404, detail="任务不存在或无法恢复")
    return Response(message="任务已恢复", data={"task_id": task_id, "status": "running"})


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    service: CompareService = Depends(get_service)
):
    """取消比对任务"""
    if not service.cancel_task(task_id):
        raise HTTPException(status_code=404, detail="任务不存在或无法取消")
    return Response(message="任务已取消", data={"task_id": task_id, "status": "cancelled"})


@router.get("/tasks/{task_id}/progress")
async def get_task_progress(
    task_id: str,
    service: CompareService = Depends(get_service)
):
    """获取任务进度"""
    data = service.get_task_progress(task_id)
    if not data:
        raise HTTPException(status_code=404, detail="任务不存在")
    return Response(data=data)


# 兼容前端API调用
@router.post("/start")
async def start_compare(
    request: CreateTaskRequest,
    service: CompareService = Depends(get_service)
):
    """启动比对（创建并启动任务）"""
    try:
        # 创建任务
        data = service.create_task(request)
        task_id = data["task_id"]
        
        # 启动任务
        await service.start_task(task_id)
        
        return Response(message="比对任务已启动", data={"taskId": task_id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/pause")
async def pause_task_alias(
    task_id: str,
    service: CompareService = Depends(get_service)
):
    """暂停比对任务（别名）"""
    if not service.pause_task(task_id):
        raise HTTPException(status_code=404, detail="任务不存在或无法暂停")
    return Response(message="任务已暂停")


@router.post("/{task_id}/resume")
async def resume_task_alias(
    task_id: str,
    service: CompareService = Depends(get_service)
):
    """恢复比对任务（别名）"""
    if not service.resume_task(task_id):
        raise HTTPException(status_code=404, detail="任务不存在或无法恢复")
    return Response(message="任务已恢复")


@router.post("/{task_id}/stop")
async def stop_task(
    task_id: str,
    service: CompareService = Depends(get_service)
):
    """停止比对任务"""
    if not service.cancel_task(task_id):
        raise HTTPException(status_code=404, detail="任务不存在或无法停止")
    return Response(message="任务已停止")
