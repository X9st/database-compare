# 数据库自动化比对工具 - 前端

基于 Electron + React + TypeScript + Ant Design 的数据库比对工具前端应用。

## 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Electron | ^28.x | 桌面应用框架 |
| React | ^18.x | UI 框架 |
| TypeScript | ^5.x | 类型安全 |
| Ant Design | ^5.x | UI 组件库 |
| Zustand | ^4.x | 状态管理 |
| Vite | ^5.x | 构建工具 |

## 项目结构

```
database-compare-front/
├── electron/               # Electron 主进程
│   ├── main.ts            # 主进程入口
│   ├── preload.ts         # 预加载脚本
│   └── ipc/               # IPC 通信
├── src/                   # React 渲染进程
│   ├── components/        # 通用组件
│   ├── pages/             # 页面组件
│   ├── stores/            # Zustand 状态
│   ├── services/          # API 服务
│   ├── hooks/             # 自定义 Hooks
│   ├── types/             # TypeScript 类型
│   └── router/            # 路由配置
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 开发环境要求

- Node.js >= 18.0.0
- npm >= 9.0.0

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 开发模式

**仅运行前端（Web 模式）：**

```bash
npm run dev
```

访问 http://localhost:3000

**运行 Electron 桌面应用：**

```bash
npm run dev:electron
```

### 3. 构建

**构建 Web 资源：**

```bash
npm run build
```

**构建 Windows 桌面应用：**

```bash
npm run build:win
```

**构建 macOS 桌面应用：**

```bash
npm run build:mac
```

## 环境配置

复制 `.env.example` 为 `.env`，根据需要修改配置：

```bash
cp .env.example .env
```

配置项说明：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| VITE_API_BASE_URL | http://localhost:18765/api/v1 | 后端 API 地址 |
| VITE_WS_BASE_URL | ws://localhost:18765 | WebSocket 地址 |

## 后端服务

前端需要配合后端服务使用，后端项目位于 `../database-compare-backend`。

请确保后端服务已启动并监听 `18765` 端口。

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动前端开发服务器 |
| `npm run dev:electron` | 启动 Electron 开发模式 |
| `npm run build` | 构建前端资源 |
| `npm run build:win` | 构建 Windows 应用 |
| `npm run build:mac` | 构建 macOS 应用 |
| `npm run lint` | TypeScript 类型检查 |
| `npm run preview` | 预览构建结果 |

## 注意事项

1. **首次运行**：请先执行 `npm install` 安装依赖
2. **后端依赖**：确保后端服务已启动，否则 API 请求会失败
3. **端口冲突**：前端默认使用 3000 端口，后端使用 18765 端口
4. **macOS 用户**：如果 5000 端口被占用，可能是 AirPlay Receiver，可在系统设置中关闭

## 打包说明

打包后的应用位于 `release/` 目录：

- Windows: `release/数据库比对工具.exe` (便携版)
- macOS: `release/数据库比对工具.dmg`
