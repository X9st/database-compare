# 多数据库 Docker 手工比对环境

这套环境用于本地手工联调，不需要在本机安装 MySQL/Oracle。

## 1. 启动方式

```bash
cd database-compare-back/dev/multidb
cp .env.example .env

docker compose up -d
```

查看启动状态：

```bash
docker compose ps
docker compose logs --no-color oracle-init
```

重置所有库（重建表和数据）：

```bash
docker compose down -v
docker compose up -d
```

## 2. 已内置的数据库（开源镜像）

- MySQL 8.4 (`127.0.0.1:33306`)
- Oracle Free 23 (`127.0.0.1:31521`, service: `FREEPDB1`)
- Inceptor / DM 通过企业镜像按需接入（见第 6 节）

## 3. 后端数据源配置建议

在系统里新增数据源时，建议按下表配置：

| 类型 | host | port | database | username | password | schema |
|---|---|---:|---|---|---|---|
| mysql | 127.0.0.1 | 33306 | qa_compare_mysql | root | Root_123456 | (留空) |
| oracle | 127.0.0.1 | 31521 | FREEPDB1 | qa_compare | OracleApp_123456 | QA_COMPARE |
| inceptor | 127.0.0.1 | 31000 | default | hive(或你配置的账号) | (按环境填写) | (留空) |

说明：
- Oracle 连接器的 `database` 字段是 service name，这里固定 `FREEPDB1`。
- Inceptor 通过 Hive2 协议接入，默认端口映射为 `31000 -> 10000`。

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
- Oracle: `cmp_oracle_only`
- Inceptor: `cmp_inceptor_only`

## 5. 推荐手工测试矩阵（MySQL/Oracle 基础）

1. `mysql -> oracle`，表：`cmp_user/cmp_order/cmp_order_item`
- 目标：验证主键、外键、唯一约束、复合主键、基础数据一致性。

2. `mysql -> oracle`，表：`cmp_data_case`
- 目标：验证 `NULL_DIFF`、`VALUE_DIFF`、浮点精度差异、大小写差异、空白差异。

3. `oracle -> mysql`，表：`cmp_struct_case`
- 目标：验证可空性、默认值、索引定义差异。

4. `oracle -> mysql`，表：`CMP_STRUCT_CASE -> cmp_struct_case`（映射模式）
- 目标：验证默认值差异、注释差异、大小写/命名映射。

5. `任意 -> 任意`，表：`cmp_order_item`
- 目标：验证复合主键分页取数与行级对比稳定性。

6. `任意 -> 任意`，表：`cmp_no_pk_log`
- 目标：验证无主键表在数据比对阶段的处理行为（通常只做结构比对）。

## 6. Inceptor 联调初始化与 UI 验收矩阵

### 6.1 启动企业镜像（按需）

仓库内提供企业扩展编排文件：

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

### 6.2 执行 Inceptor 造数脚本（default 库）

仓库已提供初始化脚本：

- `inceptor/init/01-schema-data.sql`

建议在 Inceptor 容器内通过 beeline 执行：

```bash
docker exec dbcmp-inceptor bash -lc "sudo -u hive /usr/lib/transwarp/scripts/beeline \
  -u 'jdbc:hive2://127.0.0.1:10000/default' \
  -n <inceptor_user> -p '<inceptor_password>' \
  -f /init/01-schema-data.sql"
```

脚本特性：

- 允许重复执行（`DROP TABLE IF EXISTS` + `CREATE TABLE`）
- 覆盖 `cmp_user/cmp_order/cmp_order_item/cmp_data_case/cmp_struct_case/cmp_no_pk_log/cmp_inceptor_only`
- 数据策略为“基线一致 + 可控差异”
- 除 `cmp_no_pk_log` 外其余核心表声明了逻辑主键（`PRIMARY KEY ... DISABLE NOVALIDATE`）

执行后建议跑一次连通性 smoke test：

```bash
cd /Users/asialee/database-compare/database-compare-back
python scripts/inceptor_smoke_test.py \
  --host 127.0.0.1 \
  --port 31000 \
  --database default \
  --username <inceptor_user> \
  --password '<inceptor_password>' \
  --table cmp_user
```

### 6.3 Inceptor UI 联调测试矩阵（执行顺序即验收顺序）

1. `mysql -> inceptor`，同名全量：`cmp_user/cmp_order/cmp_order_item`
- UI 参数：关闭 `compare_index` / `compare_constraint`。
- 期望：数据无差异；结构差异仅出现于 Inceptor 不支持的索引/约束维度之外的可预期项。

2. `mysql -> inceptor`，差异展示：`cmp_data_case`
- UI 参数：`trim_whitespace=false`、`ignore_case=false`、`float_precision=6`。
- 期望：出现 `value_diff`、`null_diff`、`row_missing_in_target`、`row_extra_in_target`。

3. `mysql -> inceptor`，无主键行为：`cmp_no_pk_log`
- 第一次不配置业务主键。
- 期望：出现 `primary_key_missing`。
- 第二次配置业务主键：`event_id,event_type,created_at`。
- 期望：进入正常行级比对。

4. `mysql -> inceptor`，增量模式：`cmp_order`
- UI 参数：`mode=incremental`，`time_column=order_time`，设置固定时间区间。
- 期望：只比较窗口内记录，结果口径与全量模式一致。

5. `oracle -> inceptor`，映射全量：`CMP_* -> cmp_*`
- UI 参数：`table_selection.mode=mapping`，配置表映射。
- 期望：大小写不一致可通过映射消除，结果与 MySQL 路径一致。

6. `oracle -> inceptor`，映射增量：`CMP_ORDER -> cmp_order`
- UI 参数：`time_column=ORDER_TIME`，`target_time_column=order_time`。
- 期望：目标端增量过滤生效，行级结果正确。

### 6.4 推荐配置约束（与现有接口保持一致）

- `table_selection.mode` 使用 `include` 或 `mapping`
- `options.table_mappings` 用于 Oracle 大写表名映射到 Inceptor 小写表名
- `options.table_primary_keys` 用于无物理主键表
- 增量模式使用 `options.mode=incremental` + `incremental_config.*`

文件数据源（Excel/DBF）不依赖 Docker，直接在系统里通过“数据源上传”接入。
