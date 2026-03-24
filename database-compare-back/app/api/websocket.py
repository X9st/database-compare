"""WebSocket路由"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
import asyncio
import json

from app.core.task.manager import TaskManager, CompareTask

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logger.info(f"WebSocket连接建立: task_id={task_id}")
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket连接断开: task_id={task_id}")
    
    async def broadcast(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # 移除断开的连接
            for conn in disconnected:
                self.disconnect(conn, task_id)


manager = ConnectionManager()


@router.websocket("/compare/tasks/{task_id}/progress")
async def websocket_task_progress(websocket: WebSocket, task_id: str):
    """WebSocket任务进度推送"""
    await manager.connect(websocket, task_id)
    
    task_manager = TaskManager()
    
    def progress_callback(task: CompareTask):
        """进度回调（在异步循环中调度）"""
        asyncio.create_task(send_progress(task))
    
    async def send_progress(task: CompareTask):
        """发送进度消息"""
        if task.status.value == "completed":
            message = {
                "type": "completed",
                "data": {
                    "task_id": task.id,
                    "result_id": task.result_id
                }
            }
        elif task.status.value == "failed":
            message = {
                "type": "failed",
                "data": {
                    "task_id": task.id,
                    "error_message": task.error_message
                }
            }
        else:
            message = {
                "type": "progress",
                "data": task.to_dict()
            }
        
        await manager.broadcast(task_id, message)
    
    # 注册进度回调
    task_manager.register_callback(task_id, progress_callback)
    
    try:
        while True:
            # 等待客户端消息（保持连接活跃）
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                
                # 处理心跳
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # 发送心跳检测
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        task_manager.unregister_callback(task_id)
        manager.disconnect(websocket, task_id)
