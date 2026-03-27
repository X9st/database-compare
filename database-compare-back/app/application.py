"""FastAPI应用创建"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from config import settings
from app.api.v1 import router as api_v1_router
from app.api.websocket import router as ws_router
from app.db.session import SessionLocal
from app.services.history_service import HistoryService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    db = SessionLocal()
    try:
        deleted = HistoryService(db).auto_cleanup_by_settings()
        if deleted > 0:
            logger.info(f"启动自动清理历史记录完成，删除 {deleted} 条")
    except Exception as exc:
        logger.warning(f"启动自动清理历史记录失败: {exc}")
    finally:
        db.close()
    yield
    logger.info("应用关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="数据库自动化比对工具后端API",
        lifespan=lifespan
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^null$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册API路由
    app.include_router(api_v1_router, prefix="/api/v1")
    
    # 注册WebSocket路由
    app.include_router(ws_router, prefix="/ws")
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION
        }
    
    @app.get("/version")
    async def get_version():
        import sys
        return {
            "version": settings.APP_VERSION,
            "python_version": sys.version
        }
    
    return app
