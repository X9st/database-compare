# MySQL + 达梦联调执行矩阵（上线级）

## 1. 执行约定

- 源：MySQL `source_db`（`root/root@localhost:3306`）
- 目标：DM `QA_SCHEMA`（按 `CONNECTION_INFO.md`）
- 比对建议优先使用 `include` 或 `mapping` 模式，避免大小写表名带来的全库存在性噪音
- 每条用例都要留存：请求参数、任务 ID、结果截图、关键 diff 统计

## 2. 测试矩阵

| TC | 场景 | 核心输入 | 预期结果 |
|---|---|---|---|
| TC01 | 数据源管理 | 创建 MySQL/DM 数据源并测连 | 测连成功，表列表可拉取 |
| TC02 | 全量同名比对 | `cmp_user/cmp_order/cmp_order_item` | 结构与数据无差异 |
| TC03 | 数据差异规则 | `cmp_data_case` + `ignore_case=false, trim_whitespace=false, float_precision=6` | 出现 `null_diff/value_diff/row_missing_in_target/row_extra_in_target` |
| TC04 | 选项敏感性 | 同 TC03，仅改 `ignore_case=true, trim_whitespace=true` | 差异数量下降（大小写/空白相关差异减少） |
| TC05 | 无主键行为 | `cmp_no_pk_log` 先不配业务主键，再配置业务主键 | 首次出现 `primary_key_missing`；配置后进入行级比较 |
| TC06 | 映射模式 | `table_selection.mode=mapping`，配置表名+字段映射 | 任务完成，差异与映射预期一致 |
| TC07 | 增量模式 | 配 `time_column/start_time/end_time` 或批次字段 | 只比较时间窗/批次内数据 |
| TC08 | 任务控制 | 运行中执行暂停、恢复、取消 | 状态流转正确，前端进度同步 |
| TC09 | 断点续比 | 构造失败/取消后同配置重跑 | 命中 `resume_from_task_id` 并跳过已完成表 |
| TC10 | 结果核验 | 结果页查看结构/数据/汇总并导出 | 页面展示正常，HTML/Excel/TXT 导出可用 |
| TC11 | 异常注入 | 错密码/错端口/网络阻断/超时 | 前后端返回可定位错误信息 |
| TC12 | 性能基线 | 中等数据量批量执行 | 记录每表耗时、总耗时、失败重试表现并形成阈值 |

## 3. 关键预期明细（TC03/TC04）

基于 `CMP_DATA_CASE` 与 MySQL 对比：

- `id=1`：`NULL_DIFF`（MySQL 为 `NULL`，DM 为 `'N'`）
- `id=2`：`VALUE_DIFF`（空白差异，`trim_whitespace=false` 时可见）
- `id=3`：`VALUE_DIFF`（大小写差异，`ignore_case=false` 时可见）
- `id=4`：`ROW_MISSING_IN_TARGET`
- `id=5`：`VALUE_DIFF`（数值精度差异）
- `id=6`：`ROW_EXTRA_IN_TARGET`

## 4. 缺陷记录模板

复制以下模板为每个缺陷建单：

```markdown
## 缺陷标题
[TCxx][模块] 简要问题描述

## 环境
- 日期：
- 分支/提交：
- 后端版本：
- 前端版本：
- 数据源：MySQL -> DM

## 复现步骤
1.
2.
3.

## 实际结果

## 预期结果

## 证据
- 任务ID：
- 请求参数：
- 响应片段：
- 截图/日志路径：

## 影响评估
- 严重级别：P1 / P2 / P3
- 范围：
- 是否阻断上线：
```
