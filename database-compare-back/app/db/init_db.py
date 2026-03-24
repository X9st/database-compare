"""数据库初始化"""
from loguru import logger
from app.db.session import engine
from app.models.base import Base


def init_database():
    """初始化数据库（创建所有表）"""
    logger.info("开始初始化数据库...")
    
    # 导入所有模型以确保它们被注册
    from app.models import datasource, compare_task, settings as settings_model
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    logger.info("数据库初始化完成")
