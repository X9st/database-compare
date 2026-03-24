"""应用入口"""
import uvicorn
import argparse
from app.application import create_app
from app.db.init_db import init_database
from app.utils.logger import setup_logger
from config import settings


def main():
    parser = argparse.ArgumentParser(description='数据库比对工具后端服务')
    parser.add_argument('--port', type=int, default=settings.PORT, help='服务端口')
    parser.add_argument('--host', type=str, default=settings.HOST, help='服务地址')
    args = parser.parse_args()
    
    # 配置日志
    setup_logger(settings.LOG_DIR)
    
    # 初始化数据库
    init_database()
    
    # 创建应用
    app = create_app()
    
    # 启动服务
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
