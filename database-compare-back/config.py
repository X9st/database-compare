"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "数据库比对工具"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务配置
    HOST: str = "127.0.0.1"
    PORT: int = 18765
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/db.sqlite"
    
    # 加密配置
    ENCRYPTION_KEY: Optional[str] = None
    
    # 比对配置
    DEFAULT_PAGE_SIZE: int = 10000
    MAX_DIFF_DISPLAY: int = 1000
    
    # 日志配置
    LOG_DIR: str = "data/logs"
    LOG_LEVEL: str = "INFO"
    
    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保数据目录存在
os.makedirs("data", exist_ok=True)
os.makedirs(settings.LOG_DIR, exist_ok=True)
