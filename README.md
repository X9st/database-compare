# 数据库比对工具

基于 Electron + Python 3.7 的本地桌面应用，支持多种数据库类型的表结构、字段信息和数据内容比对。

## 技术栈

- **前端**: React + Vite + Electron
- **后端**: Python 3.7 + Flask
- **数据库**: 支持 MySQL、PostgreSQL、SQLite，以及国产数据库（达梦、Inceptor 等）

## 项目结构

```
database-compare/
├── src/
│   ├── main/                    # Electron 主进程
│   │   ├── main.js             # 主入口
│   │   └── preload.js          # 预加载脚本
│   ├── renderer/               # Electron 渲染进程（前端）
│   │   ├── index.html
│   │   ├── src/
│   │   │   ├── main.jsx        # React 入口
│   │   │   ├── App.jsx         # 主应用组件
│   │   │   ├── App.css         # 样式
│   │   │   ├── index.css
│   │   │   └── components/     # 组件目录
│   │   │       ├── ConnectionManager.jsx
│   │   │       ├── ComparisonTask.jsx
│   │   │       └── ResultDisplay.jsx
│   │   └── dist/               # 构建输出
│   └── python-service/         # Python 后端服务
│       ├── requirements.txt
│       └── src/
│           ├── app.py          # Flask 应用入口
│           ├── database.py     # 数据库管理
│           ├── comparator.py   # 比对逻辑
│           └── storage.py      # 数据存储
├── package.json
├── vite.config.js
└── electron-builder.json
```

## 开发环境准备

### 1. 安装 Node.js 依赖

```bash
npm install
```

### 2. 安装 Python 依赖

```bash
cd src/python-service
pip install -r requirements.txt
```

### 3. 启动开发服务器

**终端 1 - 启动前端开发服务器:**
```bash
npm run dev
```

**终端 2 - 启动 Python 后端:**
```bash
cd src/python-service
python src/app.py
```

**终端 3 - 启动 Electron:**
```bash
npm run electron:dev
```

## 打包发布

### 构建前端

```bash
npm run build
```

### 打包 Electron 应用

```bash
# 打包当前平台
npm run electron:build

# 打包所有平台
npm run dist
```

打包后的应用位于 `release/` 目录。

## 离线部署说明

### 前端离线部署
- 所有前端依赖通过 npm 安装并打包到应用内
- 不使用任何 CDN 资源
- 构建后所有资源包含在应用包中

### Python 环境离线部署
1. 预先下载所有依赖包:
```bash
pip download -r requirements.txt -d dependencies/
```

2. 离线安装:
```bash
pip install --no-index --find-links=dependencies -r requirements.txt
```

3. 国产数据库驱动（如 dmPython）需要手动下载 whl 文件并放置到 dependencies 目录

## 功能特性

- [x] 多数据库连接管理
- [x] 表结构比对
- [x] 字段信息比对
- [ ] 数据内容比对
- [ ] 国产数据库支持（达梦、Inceptor）
- [ ] 报告导出（HTML/Excel/PDF）
- [ ] 历史记录管理

## 支持的数据库

### 国际数据库
- MySQL / MariaDB
- PostgreSQL
- SQLite

### 国产数据库
- 达梦数据库 (DM) - 需手动安装 dmPython
- Inceptor (星环信息) - 需手动安装 pyhive
- 人大金仓 (Kingbase) - 直接使用，兼容 PostgreSQL 协议

## 国产数据库驱动安装

### 达梦数据库 (DM)

达梦数据库驱动需要从达梦官网下载，无法通过 pip 直接安装。

1. 从达梦官网下载对应版本的 dmPython 驱动
2. 安装驱动：
```bash
pip install /path/to/dmPython-2.5.5-py3-none-any.whl
```

3. 验证安装：
```bash
python -c "import dmPython; print('dmPython 安装成功')"
```

### Inceptor (星环信息)

Inceptor 使用 pyhive 驱动连接：

```bash
pip install pyhive==0.7.0 thrift==0.16.0 sasl==0.3.0 pure-sasl==0.6.2
```

注意：sasl 依赖系统库，可能需要先安装：
- macOS: `brew install cyrus-sasl`
- Ubuntu: `apt-get install libsasl2-dev`
- CentOS: `yum install cyrus-sasl-devel`

### 人大金仓 (Kingbase)

人大金仓兼容 PostgreSQL 协议，无需额外安装驱动，使用 psycopg2 即可连接。

默认端口：54321

## 许可证

MIT
