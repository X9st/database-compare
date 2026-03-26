# 多数据库 Docker 手工比对环境

这套环境用于本地手工联调，不需要在本机安装 MySQL/PostgreSQL/SQL Server/Oracle。

## 1. 启动方式

```bash
cd database-compare-back/dev/multidb
cp .env.example .env

docker compose up -d
```

查看启动状态：

```bash
docker compose ps
docker compose logs --no-color sqlserver-init oracle-init
```

重置所有库（重建表和数据）：

```bash
docker compose down -v
docker compose up -d
```

## 2. 已内置的数据库

- MySQL 8.4 (`127.0.0.1:33306`)
- PostgreSQL 16 (`127.0.0.1:35432`)
- SQL Server 2022 (`127.0.0.1:31433`)
- Oracle Free 23 (`127.0.0.1:31521`, service: `FREEPDB1`)

## 3. 后端数据源配置建议

在系统里新增数据源时，建议按下表配置：

| 类型 | host | port | database | username | password | schema |
|---|---|---:|---|---|---|---|
| mysql | 127.0.0.1 | 33306 | qa_compare_mysql | root | Root_123456 | (留空) |
| postgresql | 127.0.0.1 | 35432 | qa_compare_pg | postgres | Postgres_123456 | qa_compare |
| sqlserver | 127.0.0.1 | 31433 | qa_compare_mssql | sa | SqlServer_123456 | dbo |
| oracle | 127.0.0.1 | 31521 | FREEPDB1 | qa_compare | OracleApp_123456 | QA_COMPARE |

说明：
- Oracle 连接器的 `database` 字段是 service name，这里固定 `FREEPDB1`。
- PostgreSQL 建议填写 `schema=qa_compare`，避免落到 `public`。

## 4. 初始化后包含的测试对象

每个库都包含一组核心表（语义对齐）：

- `cmp_user`
- `cmp_order`
- `cmp_order_item`（复合主键）
- `cmp_data_case`（空值/精度/大小写/空格差异）
- `cmp_struct_case`（刻意制造结构差异）
- `cmp_no_pk_log`（无主键行为）

每个库还包含一个库特有表（用于验证异构场景中的对象差异）：

- MySQL: `cmp_mysql_only`
- PostgreSQL: `cmp_pg_only`
- SQL Server: `cmp_mssql_only`
- Oracle: `cmp_oracle_only`

## 5. 推荐手工测试矩阵

1. `mysql -> postgresql`，表：`cmp_user/cmp_order/cmp_order_item`
- 目标：验证主键、外键、唯一约束、复合主键、基础数据一致性。

2. `mysql -> postgresql`，表：`cmp_data_case`
- 目标：验证 `NULL_DIFF`、`VALUE_DIFF`、浮点精度差异、大小写差异、空白差异。

3. `mysql -> sqlserver`，表：`cmp_struct_case`
- 目标：验证可空性、默认值、索引定义差异。

4. `oracle -> postgresql`，表：`CMP_STRUCT_CASE -> cmp_struct_case`（映射模式）
- 目标：验证长度差异、默认值差异、注释差异、大小写/命名映射。

5. `任意 -> 任意`，表：`cmp_order_item`
- 目标：验证复合主键分页取数与行级对比稳定性。

6. `任意 -> 任意`，表：`cmp_no_pk_log`
- 目标：验证无主键表在数据比对阶段的处理行为（通常只做结构比对）。

## 6. 关于 DM / Inceptor

仓库内提供了模板文件，但默认不启动：

- `docker-compose.enterprise-template.yml`
- `dm/init/README.md`
- `inceptor/init/README.md`

如果你们有内部可用镜像，可这样接入：

```bash
export DM_IMAGE=<your_dm_image>
export INCEPTOR_IMAGE=<your_inceptor_image>

docker compose \
  -f docker-compose.yml \
  -f docker-compose.enterprise-template.yml \
  --profile enterprise up -d
```

然后按同名表规范在 `dm/init`、`inceptor/init` 放初始化脚本，即可并入同一套手工比对流程。
