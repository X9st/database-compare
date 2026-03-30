"""数据库初始化"""
from loguru import logger
from sqlalchemy import inspect, text
from app.db.session import engine
from app.models.base import Base


def _ensure_datasource_extra_config_column() -> None:
    """兼容升级：为已有 datasources 表补齐 extra_config 列。"""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "datasources" not in table_names:
        return

    columns = {col["name"] for col in inspector.get_columns("datasources")}
    if "extra_config" in columns:
        return

    logger.info("检测到 datasources 缺少 extra_config 列，开始执行兼容升级")
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE datasources ADD COLUMN extra_config JSON"))
    logger.info("datasources.extra_config 列补齐完成")


def init_database():
    """初始化数据库（创建所有表）"""
    logger.info("开始初始化数据库...")
    
    # 导入所有模型以确保它们被注册
    from app.models import datasource, compare_task, settings as settings_model
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    _ensure_datasource_extra_config_column()
    
    logger.info("数据库初始化完成")
