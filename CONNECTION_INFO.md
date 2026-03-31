# 服务器与达梦数据库连接信息

更新时间：2026-03-30

## 1) Linux 服务器（SSH）

- 云厂商：阿里云 ECS
- 主机名：`iZzeh3jd1bc4w3i4snt34Z`
- 公网 IP：`39.105.124.246`
- SSH 端口：`22`
- 登录用户：`root`

SSH 连接命令：

```bash
ssh root@39.105.124.246 -p 22
```

## 2) 达梦数据库（DM8）

- 数据库类型：达梦 `DM8`
- 实例名：`DM8`
- 服务名（systemd）：`DmServiceDMSERVER`
- 监听端口：`5236`
- 安装目录：`/opt/dmdbms`
- 数据目录：`/opt/dmdbms/data/DM8`
- 配置文件：`/opt/dmdbms/data/DM8/dm.ini`

本机登录（服务器内）：

```bash
/opt/dmdbms/bin/disql SYSDBA/'<请填写新密码>'@127.0.0.1:5236
```

远程连接参数（客户端工具如 DBeaver/Navicat）：

- Host：`39.105.124.246`
- Port：`5236`
- User：`SYSDBA`
- Password：`AAAaaa11`
- Database/Schema：`DM8`（如客户端要求填写）

---

## 3) Inceptor（TDH/Quark）连接信息（Python 项目可用）

更新时间：2026-03-31

### 3.1 本次部署实测结果

- TDH 容器：`tdh-dev`（镜像：`tdh-standalone:2024.5`）
- 管理台：`http://39.105.124.246:8180`
- Inceptor 服务（Quark Server）状态：`active`
- 关键端口：
  - `10000`（Hive2 / Inceptor SQL）
  - `9083`（Metastore）
  - `2181`（ZooKeeper）
  - `8888`（Quark SparkUI）
- 宝塔面板端口冲突已处理：宝塔已改到 `18887`，避免占用 `8888`

### 3.2 你项目里 Inceptor 的真实接入方式（非 JDBC 代码）

项目后端是 Python，Inceptor 通过 `pyhive` 连接（不是在业务代码里直接写 JDBC）：

- 连接器实现：`database-compare-back/app/core/connector/inceptor.py`
- 依赖：`pyhive==0.7.0`、`thrift==0.16.0`、`thrift_sasl==0.4.3`
- 认证策略（代码中）：
  - 有密码时：`auth='LDAP'`
  - 无密码时：`auth='NONE'`

### 3.3 项目内数据源配置（前后端一致）

前端 `Inceptor` 默认端口是 `10000`，后端测试连接必填项是：

- `db_type`: `inceptor`
- `host`
- `port`
- `database`（推荐 `default`）
- `username`
- `password`
- 可选：`charset`（默认 `UTF-8`）、`timeout`（默认 `30`）

建议用于本项目的连接参数：

- Host：`39.105.124.246`（若后端与数据库同机也可填 `127.0.0.1`）
- Port：`10000`
- Database：`default`
- Username：`admin`
- Password：`AAAaaa11`
- Charset：`UTF-8`
- Timeout：`30`

### 3.4 Python 直连示例（项目外独立测试）

```python
from pyhive import hive

conn = hive.connect(
    host="39.105.124.246",
    port=10000,
    username="admin",
    password="AAAaaa11",
    database="default",
    auth="LDAP",
)
cur = conn.cursor()
cur.execute("select 1")
print(cur.fetchall())
cur.close()
conn.close()
```

### 3.5 项目内 Smoke Test 命令

```bash
cd /Users/asialee/database-compare/database-compare-back
python scripts/inceptor_smoke_test.py \
  --host 39.105.124.246 \
  --port 10000 \
  --database default \
  --username admin \
  --password 'AAAaaa11' \
  --table cmp_user
```

### 3.6 常用运维命令（Inceptor）

查看关键服务状态：

```bash
docker exec tdh-dev bash -lc "systemctl is-active transwarp-quark-server@quark1 transwarp-quark-metastore@quark1 transwarp-zookeeper@zookeeper1"
```

查看关键端口：

```bash
docker exec tdh-dev bash -lc "ss -lntp | grep -E ':8180|:2181|:9083|:10000|:8888' || true"
```

查看 Quark Server 日志：

```bash
docker exec tdh-dev bash -lc "journalctl -u transwarp-quark-server@quark1 --no-pager -n 200"
docker exec tdh-dev bash -lc "tail -n 200 /var/log/quark1/quark-server.log"
```

SQL 连通性（运维验证命令）：

```bash
docker exec tdh-dev bash -lc "sudo -u hive /usr/lib/transwarp/scripts/beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n admin -p 'AAAaaa11' -e 'select 1;'"
```

### 3.7 这次排障结论（便于后续复用）

- 失败根因：`Quark Server` 启动时 `SparkUI 8888` 与 `BT-Panel` 端口冲突
- 典型报错：`Failed to bind SparkUI` / `Address already in use`
- 解决动作：
  - 暂停宝塔：`bt stop`
  - 完成安装后改宝塔端口：`echo 18887 > /www/server/panel/data/port.pl && bt restart`
  - 确认 `8888` 被 Quark 占用，`18887` 被宝塔占用

### 3.8 对你这个 Python 项目的结论

- 你项目可以直接使用现有 `InceptorConnector`（`pyhive`）
- 不需要在业务代码中手写 JDBC 驱动
- JDBC URL 主要用于客户端工具或 beeline 运维验证；Python 代码按 `host/port/database/username/password` 即可

### 3.9 补充项（远程服务器关键信息，已补齐）

以下是之前未明确写出的关键部署信息，现补充如下：

- 远程服务器内网 IP：`172.24.56.81`
- TDH 镜像包路径：`/opt/tdh-2024.5.tar`
- TDH 容器数据挂载目录：`/data/tdh/transwarp`（容器内挂载点 `/opt/transwarp`）
- 容器运行方式：`--network host`（与宿主机端口共用，需避免端口冲突）
- 宝塔面板当前端口：`18887`（已从 `8888` 迁移）
- beeline 实际可执行路径：`/usr/lib/transwarp/scripts/beeline`（不在默认 PATH）
- Inceptor SQL 连通性实测：`select 1` 返回 `1`

建议在阿里云安全组/本机防火墙确认放行端口：

- `22`（SSH）
- `8180`（TDH Manager）
- `10000`（Inceptor SQL）
- `5236`（DM8，如需外部访问）
- `18887`（宝塔面板，如需外部访问）

快速核对命令（远程服务器执行）：

```bash
ss -lntp | grep -E ':22|:8180|:10000|:5236|:18887|:8888' || true
docker ps --filter name=tdh-dev
docker exec tdh-dev bash -lc "systemctl is-active transwarp-quark-server@quark1 transwarp-quark-metastore@quark1 transwarp-zookeeper@zookeeper1"
docker exec tdh-dev bash -lc "sudo -u hive /usr/lib/transwarp/scripts/beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n admin -p 'AAAaaa11' -e 'select 1;'"
```

项目部署建议（避免走公网）：

- 如果后端服务与 Inceptor 在同一台服务器，优先使用 `127.0.0.1:10000`
- 仅在本地开发机直连时使用 `39.105.124.246:10000`
