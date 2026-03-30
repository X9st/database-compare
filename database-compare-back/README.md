# 数据库比对工具后端

## 简介

这是数据库自动化比对工具的后端服务，基于 FastAPI 构建。

## 技术栈

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- SQLite
- PyMySQL / oracledb / dmPython / pyhive

## 支持的数据源类型

- 数据库：`mysql`、`oracle`、`dm`、`inceptor`
- 文件：`excel`（`.xlsx/.xls`）、`dbf`

## 快速开始

### 安装依赖

```bash
cd database-compare-back
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 运行服务

```bash
python main.py
```

服务将在 http://localhost:18765 启动。

### 推荐启动方式（固定加密密钥路径）

为避免历史数据源密码因密钥路径漂移导致解密失败，建议使用：

```bash
./scripts/start_backend.sh
```

该脚本会自动固定 `ENCRYPTION_KEY_FILE` 到后端目录下的 `data/encryption.key`。

### API 文档

启动服务后，访问：
- Swagger UI: http://localhost:18765/docs
- ReDoc: http://localhost:18765/redoc

## 项目结构

```
database-compare-back/
├── main.py                 # 入口文件
├── config.py               # 配置管理
├── requirements.txt        # 依赖清单
├── app/
│   ├── application.py      # FastAPI 应用
│   ├── api/                # API 路由
│   │   ├── v1/
│   │   │   ├── datasource.py
│   │   │   ├── compare.py
│   │   │   ├── result.py
│   │   │   ├── history.py
│   │   │   └── settings.py
│   │   └── websocket.py
│   ├── schemas/            # Pydantic 模型
│   ├── services/           # 业务服务层
│   ├── models/             # SQLAlchemy 模型
│   ├── core/               # 核心功能
│   │   ├── connector/      # 数据库连接器
│   │   ├── comparator/     # 比对器
│   │   ├── exporter/       # 导出器
│   │   └── task/           # 任务管理
│   ├── db/                 # 数据库会话
│   └── utils/              # 工具类
└── data/                   # 数据目录
    ├── db.sqlite           # SQLite 数据库
    └── logs/               # 日志目录
```

## API 概览

### 数据源管理
- `GET /api/v1/datasources` - 获取数据源列表
- `POST /api/v1/datasources` - 创建数据源
- `POST /api/v1/datasources/files/upload` - 上传 Excel/DBF 数据源文件
- `PUT /api/v1/datasources/{id}` - 更新数据源
- `DELETE /api/v1/datasources/{id}` - 删除数据源
- `POST /api/v1/datasources/{id}/test` - 测试连接
- `GET /api/v1/datasources/{id}/tables` - 获取表列表

### 比对任务
- `POST /api/v1/compare/tasks` - 创建比对任务
- `POST /api/v1/compare/tasks/{id}/start` - 启动任务
- `POST /api/v1/compare/tasks/{id}/pause` - 暂停任务
- `POST /api/v1/compare/tasks/{id}/cancel` - 取消任务
- `GET /api/v1/compare/tasks/{id}/progress` - 获取进度

### 比对结果
- `GET /api/v1/compare/results/{id}` - 获取结果
- `GET /api/v1/compare/results/{id}/structure-diffs` - 获取结构差异
- `GET /api/v1/compare/results/{id}/data-diffs` - 获取数据差异

### WebSocket
- `ws://localhost:18765/ws/compare/tasks/{id}/progress` - 实时进度推送
