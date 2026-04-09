# Windows 离线内网部署手册（MySQL + 达梦联调）

## 1. 目标

在 Windows 主机上完成以下就绪项：

- Python 后端可运行
- `dmPython` 驱动可导入
- MySQL/DM 两类数据源可测连、可拉表
- 前端可连后端进行联调

## 2. 基础前提

- 操作系统：Windows 10/11 或 Windows Server
- Python：3.11+
- Node.js：18+
- 后端目录：`database-compare-back`
- 前端目录：`database-compare-front`
- MySQL：`localhost:3306/source_db`
- DM：按 `CONNECTION_INFO.md` 提供的连接信息

## 3. 后端环境安装

```powershell
cd d:\database-compare\database-compare-back
d:\database-compare\.python311\python.exe -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. 达梦驱动安装

### 4.1 在线安装（当前环境）

```powershell
.\venv\Scripts\python.exe -m pip install dmPython
```

### 4.2 离线安装（内网推荐）

1. 在有网机器下载 wheel（版本示例：`dmpython-2.5.30-cp311-cp311-win_amd64.whl`）。
2. 拷贝到内网机器，例如 `d:\offline_pkgs\`.
3. 内网安装：

```powershell
.\venv\Scripts\python.exe -m pip install d:\offline_pkgs\dmpython-2.5.30-cp311-cp311-win_amd64.whl
```

### 4.3 驱动验收

```powershell
.\venv\Scripts\python.exe -c "import dmPython; print('dmPython import ok')"
```

## 5. 数据初始化

### 5.1 MySQL 源库

执行脚本：`dev/multidb/mysql/init/01-schema-data.sql`

关键结果应为：

- `cmp_user=4`
- `cmp_order=3`
- `cmp_order_item=4`
- `cmp_data_case=5`
- `cmp_struct_case=2`
- `cmp_no_pk_log=2`
- `cmp_mysql_only=1`

### 5.2 达梦目标库（QA_SCHEMA）

在达梦服务器执行：

1. `dev/multidb/dm/init/00-create-qa-schema.sql`
2. `dev/multidb/dm/init/01-schema-data.sql`
3. `dev/multidb/dm/init/02-verify.sql`

## 6. 启动服务

### 6.1 后端

```powershell
cd d:\database-compare\database-compare-back
.\venv\Scripts\Activate.ps1
python main.py
```

默认：`http://localhost:18765`

### 6.2 前端

```powershell
cd d:\database-compare\database-compare-front
npm install
Copy-Item .env.example .env -Force
npm run dev
```

默认：`http://localhost:3000`

## 7. 联调探活（TC01 前置）

后端直连测试：

- `POST /api/v1/datasources/test`（MySQL）
- `POST /api/v1/datasources/test`（DM）
- `GET /api/v1/datasources/{id}/tables`

推荐直接运行脚本：

```powershell
cd d:\database-compare\database-compare-back
.\venv\Scripts\python.exe scripts\mysql_dm_api_probe.py `
  --base-url http://localhost:18765 `
  --mysql-password root `
  --dm-host 39.105.124.246 `
  --dm-port 5236 `
  --dm-user SYSDBA `
  --dm-password AAAaaa11 `
  --dm-database DM8 `
  --dm-schema QA_SCHEMA
```

## 8. 常见问题

- `创建SOCKET连接失败`：优先检查 DM 服务端监听、云安全组、防火墙、白名单、网络策略。
- 连接成功但拉表为空：检查数据源 `schema` 是否为 `QA_SCHEMA`。
- 全库模式表存在差异异常偏多：MySQL 小写表名与 DM 大写表名可能产生“存在性差异”，联调建议先用 `include` 或 `mapping` 模式。
