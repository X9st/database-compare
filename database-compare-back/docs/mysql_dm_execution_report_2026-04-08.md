# MySQL + 达梦联调执行报告（2026-04-08）

## 1. 本次已完成交付

- 达梦初始化脚本：
  - `dev/multidb/dm/init/00-create-qa-schema.sql`
  - `dev/multidb/dm/init/01-schema-data.sql`
  - `dev/multidb/dm/init/02-verify.sql`
- 自动执行脚本：
  - `scripts/dm_exec_sql_file.py`
  - `scripts/mysql_dm_api_probe.py`
- 文档：
  - `docs/windows_dm_offline_setup.md`
  - `docs/mysql_dm_joint_test_matrix.md`
  - `docs/mysql_dm_go_no_go_checklist.md`
- 连接器修复：
  - `app/core/connector/dm.py` 改为 DSN 连接并显式 `SET SCHEMA`
- 任务控制修复：
  - `app/core/comparator/data.py` 增加分页级取消检查
  - `app/services/compare_service.py` 接入 `ComparisonCancelled` 并统一落库 `cancelled`

## 2. 环境执行结果

- `dmPython`：已安装（`2.5.30` wheel）
- MySQL `source_db`：已执行标准初始化脚本，7 张 `cmp_*` 表行数匹配预期
- 达梦 `QA_SCHEMA`：已执行 `00/01/02`，`dm_smoke_test.py` 通过
- 前后端启动探活：
  - `/health` 可用
  - `/api/v1/datasources/test`（MySQL/DM）可用
  - `/api/v1/datasources/{id}/tables`（MySQL/DM）可用
  - 前端 `/`, `/compare`, `/datasource` 返回正常 HTML

## 3. 用例执行状态

| TC | 状态 | 结果摘要 |
|---|---|---|
| TC01 | 通过 | 建源、测连、拉表均通过 |
| TC02 | 通过（有结构差异） | `cmp_user/cmp_order/cmp_order_item` 数据差异为 0，结构差异较多（类型/长度/注释/索引/约束） |
| TC03 | 通过 | `cmp_data_case` 出现 `null_diff/value_diff/row_missing_in_target/row_extra_in_target` |
| TC04 | 通过 | 开启 `ignore_case + trim_whitespace` 后数据差异从 6 降至 4 |
| TC05 | 通过 | 无业务主键时 `primary_key_missing`；配置业务主键后数据差异为 0 |
| TC06 | 通过 | mapping 模式可执行，任务完成 |
| TC07 | 通过 | incremental 模式可执行，任务完成 |
| TC08 | 通过 | `pause/resume/cancel` 均已验证，`cancel` 可在单表分页比对过程中生效 |
| TC09 | 通过 | 新任务返回 `resume_from_task_id`，命中断点续比 |
| TC10 | 通过 | `txt/html/excel` 三种导出成功，文件落地存在 |
| TC11 | 通过（提示文案待优化） | 错密码/错端口均失败返回；错误信息当前存在乱码 |
| TC12 | 未完成 | 尚未进行系统化性能压测与阈值固化 |

## 4. 发现的问题与风险

1. 达梦错误文案可读性不足：
- `dmPython` 异常字符串在部分路径出现乱码。
- 建议：捕获异常后增加统一编码与友好错误映射。

2. 结构差异噪音较大：
- MySQL 与 DM 异构导致长度/类型/注释/索引/约束差异较多，属于预期但会影响“纯数据对齐”阅读。
- 建议：按业务场景启用忽略规则模板（列类型、注释、索引类差异）。
