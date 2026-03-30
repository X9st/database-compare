# 数据库自动化比对工具 - API接口设计文档

## 文档信息

| 属性 | 内容 |
|------|------|
| 文档版本 | V1.0 |
| 编写日期 | 2026-03-24 |
| 基础地址 | http://localhost:18765/api/v1 |

---

# 1. 接口规范

## 1.1 请求规范

- **协议**：HTTP/HTTPS
- **编码**：UTF-8
- **格式**：JSON
- **方法**：GET / POST / PUT / DELETE

## 1.2 响应规范

### 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 分页响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": [],
  "page_info": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### 错误码定义

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 资源不存在 |
| 1003 | 资源已存在 |
| 2001 | 数据库连接失败 |
| 2002 | 数据库查询失败 |
| 2003 | 数据库权限不足 |
| 3001 | 比对任务不存在 |
| 3002 | 比对任务执行失败 |
| 3003 | 比对任务已取消 |
| 9999 | 系统错误 |

---

# 2. 数据源管理接口

## 2.1 获取数据源列表

**请求**

```
GET /datasources
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| group_id | string | 否 | 分组ID筛选 |
| keyword | string | 否 | 关键词搜索（名称、主机） |
| db_type | string | 否 | 数据库类型筛选 |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "ds_001",
      "name": "生产环境-MySQL",
      "group_id": "grp_001",
      "group_name": "生产环境",
      "db_type": "mysql",
      "host": "192.168.1.100",
      "port": 3306,
      "database": "business_db",
      "schema": null,
      "username": "readonly",
      "charset": "UTF-8",
      "timeout": 30,
      "created_at": "2026-03-20T10:00:00Z",
      "updated_at": "2026-03-20T10:00:00Z"
    }
  ]
}
```

---

## 2.2 获取单个数据源

**请求**

```
GET /datasources/{id}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 数据源ID |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "ds_001",
    "name": "生产环境-MySQL",
    "group_id": "grp_001",
    "group_name": "生产环境",
    "db_type": "mysql",
    "host": "192.168.1.100",
    "port": 3306,
    "database": "business_db",
    "schema": null,
    "username": "readonly",
    "charset": "UTF-8",
    "timeout": 30,
    "created_at": "2026-03-20T10:00:00Z",
    "updated_at": "2026-03-20T10:00:00Z"
  }
}
```

---

## 2.3 创建数据源

**请求**

```
POST /datasources
```

**请求体**

```json
{
  "name": "生产环境-MySQL",
  "group_id": "grp_001",
  "db_type": "mysql",
  "host": "192.168.1.100",
  "port": 3306,
  "database": "business_db",
  "schema": null,
  "username": "readonly",
  "password": "your_password",
  "charset": "UTF-8",
  "timeout": 30
}
```

**请求参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 数据源名称，最长100字符 |
| group_id | string | 否 | 所属分组ID |
| db_type | string | 是 | 数据库类型：mysql/oracle/dm/inceptor/excel/dbf |
| host | string | 是 | 主机地址 |
| port | integer | 是 | 端口号 |
| database | string | 是 | 数据库名 |
| schema | string | 否 | Schema名（Oracle需要） |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| charset | string | 否 | 字符集，默认UTF-8 |
| timeout | integer | 否 | 连接超时秒数，默认30 |

**响应示例**

```json
{
  "code": 0,
  "message": "创建成功",
  "data": {
    "id": "ds_001",
    "name": "生产环境-MySQL",
    "db_type": "mysql",
    "host": "192.168.1.100",
    "port": 3306,
    "database": "business_db",
    "created_at": "2026-03-20T10:00:00Z"
  }
}
```

---

## 2.4 更新数据源

**请求**

```
PUT /datasources/{id}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 数据源ID |

**请求体**

```json
{
  "name": "生产环境-MySQL-更新",
  "port": 3307,
  "password": "new_password"
}
```

**说明**：仅需传入需要更新的字段

**响应示例**

```json
{
  "code": 0,
  "message": "更新成功",
  "data": {
    "id": "ds_001",
    "name": "生产环境-MySQL-更新",
    "port": 3307,
    "updated_at": "2026-03-21T10:00:00Z"
  }
}
```

---

## 2.5 删除数据源

**请求**

```
DELETE /datasources/{id}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 数据源ID |

**响应示例**

```json
{
  "code": 0,
  "message": "删除成功",
  "data": null
}
```

---

## 2.6 测试数据源连接

**请求**

```
POST /datasources/{id}/test
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 数据源ID |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "success": true,
    "message": "连接成功",
    "latency": 23,
    "version": "MySQL 8.0.32"
  }
}
```

**连接失败响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "success": false,
    "message": "Access denied for user 'readonly'@'192.168.1.1' (using password: YES)",
    "latency": null,
    "version": null
  }
}
```

---

## 2.7 测试连接（不保存）

**请求**

```
POST /datasources/test-connection
```

**请求体**

```json
{
  "db_type": "mysql",
  "host": "192.168.1.100",
  "port": 3306,
  "database": "business_db",
  "username": "readonly",
  "password": "your_password",
  "charset": "UTF-8",
  "timeout": 30
}
```

**响应示例**：同 2.6

---

## 2.8 获取数据库表列表

**请求**

```
GET /datasources/{id}/tables
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 数据源ID |

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| schema | string | 否 | Schema名称筛选 |
| keyword | string | 否 | 表名关键词搜索 |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "name": "t_user",
      "schema": "public",
      "comment": "用户表",
      "row_count": 10000
    },
    {
      "name": "t_order",
      "schema": "public",
      "comment": "订单表",
      "row_count": 500000
    }
  ]
}
```

---

## 2.9 获取表结构信息

**请求**

```
GET /datasources/{id}/tables/{table_name}/schema
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 数据源ID |
| table_name | string | 是 | 表名 |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "table_name": "t_user",
    "comment": "用户表",
    "columns": [
      {
        "name": "id",
        "data_type": "bigint",
        "length": null,
        "precision": 20,
        "scale": 0,
        "nullable": false,
        "default_value": null,
        "comment": "主键ID",
        "is_primary_key": true
      },
      {
        "name": "username",
        "data_type": "varchar",
        "length": 50,
        "precision": null,
        "scale": null,
        "nullable": false,
        "default_value": null,
        "comment": "用户名",
        "is_primary_key": false
      }
    ],
    "indexes": [
      {
        "name": "PRIMARY",
        "columns": ["id"],
        "is_unique": true,
        "is_primary": true,
        "index_type": "BTREE"
      },
      {
        "name": "idx_username",
        "columns": ["username"],
        "is_unique": true,
        "is_primary": false,
        "index_type": "BTREE"
      }
    ],
    "constraints": [
      {
        "name": "PRIMARY",
        "constraint_type": "PRIMARY KEY",
        "columns": ["id"],
        "reference_table": null,
        "reference_columns": null
      }
    ]
  }
}
```

---

# 3. 数据源分组接口

## 3.1 获取分组列表

**请求**

```
GET /datasource-groups
```

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "grp_001",
      "name": "生产环境",
      "count": 5,
      "sort_order": 1
    },
    {
      "id": "grp_002",
      "name": "测试环境",
      "count": 3,
      "sort_order": 2
    }
  ]
}
```

---

## 3.2 创建分组

**请求**

```
POST /datasource-groups
```

**请求体**

```json
{
  "name": "开发环境"
}
```

**响应示例**

```json
{
  "code": 0,
  "message": "创建成功",
  "data": {
    "id": "grp_003",
    "name": "开发环境",
    "count": 0,
    "sort_order": 3
  }
}
```

---

## 3.3 更新分组

**请求**

```
PUT /datasource-groups/{id}
```

**请求体**

```json
{
  "name": "开发环境-新",
  "sort_order": 1
}
```

---

## 3.4 删除分组

**请求**

```
DELETE /datasource-groups/{id}
```

**说明**：删除分组不会删除该分组下的数据源，数据源的group_id会置为null

---

# 4. 比对任务接口

## 4.1 创建比对任务

**请求**

```
POST /compare/tasks
```

**请求体**

```json
{
  "source_id": "ds_001",
  "target_id": "ds_002",
  "table_selection": {
    "mode": "include",
    "tables": ["t_user", "t_order", "t_product"]
  },
  "options": {
    "mode": "full",
    "incremental_config": null,
    "structure_options": {
      "compare_index": true,
      "compare_constraint": true,
      "compare_comment": true
    },
    "data_options": {
      "float_precision": 6,
      "ignore_case": false,
      "trim_whitespace": true,
      "datetime_precision": "second",
      "skip_large_fields": true,
      "page_size": 10000
    },
    "table_mappings": [
      {
        "source_table": "t_user",
        "target_table": "user_info",
        "column_mappings": [
          {"source_column": "user_name", "target_column": "username"}
        ]
      }
    ],
    "ignore_rules": ["rule_001", "rule_002"]
  }
}
```

**请求参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_id | string | 是 | 源数据源ID |
| target_id | string | 是 | 目标数据源ID |
| table_selection | object | 是 | 表选择配置 |
| table_selection.mode | string | 是 | 选择模式：all/include/exclude |
| table_selection.tables | array | 否 | 表名列表（mode为include/exclude时必填） |
| options | object | 是 | 比对选项 |
| options.mode | string | 是 | 比对模式：full/incremental |
| options.incremental_config | object | 否 | 增量配置（mode为incremental时必填） |
| options.structure_options | object | 否 | 结构比对选项 |
| options.data_options | object | 否 | 数据比对选项 |
| options.table_mappings | array | 否 | 表映射配置 |
| options.ignore_rules | array | 否 | 忽略规则ID列表 |

**增量配置参数**

```json
{
  "incremental_config": {
    "time_column": "update_time",
    "start_time": "2026-03-20T00:00:00Z",
    "end_time": "2026-03-21T00:00:00Z"
  }
}
```

**响应示例**

```json
{
  "code": 0,
  "message": "任务创建成功",
  "data": {
    "task_id": "task_001",
    "status": "pending",
    "created_at": "2026-03-20T10:00:00Z"
  }
}
```

---

## 4.2 启动比对任务

**请求**

```
POST /compare/tasks/{task_id}/start
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务ID |

**响应示例**

```json
{
  "code": 0,
  "message": "任务已启动",
  "data": {
    "task_id": "task_001",
    "status": "running"
  }
}
```

---

## 4.3 暂停比对任务

**请求**

```
POST /compare/tasks/{task_id}/pause
```

**响应示例**

```json
{
  "code": 0,
  "message": "任务已暂停",
  "data": {
    "task_id": "task_001",
    "status": "paused"
  }
}
```

---

## 4.4 恢复比对任务

**请求**

```
POST /compare/tasks/{task_id}/resume
```

---

## 4.5 取消比对任务

**请求**

```
POST /compare/tasks/{task_id}/cancel
```

---

## 4.6 获取任务状态和进度

**请求**

```
GET /compare/tasks/{task_id}/progress
```

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_001",
    "status": "running",
    "progress": {
      "total_tables": 10,
      "completed_tables": 3,
      "current_table": "t_order",
      "current_phase": "data",
      "percentage": 35.5,
      "start_time": "2026-03-20T10:00:00Z",
      "elapsed_seconds": 120,
      "estimated_remaining_seconds": 220
    }
  }
}
```

**任务状态说明**

| 状态 | 说明 |
|------|------|
| pending | 待执行 |
| running | 执行中 |
| paused | 已暂停 |
| completed | 已完成 |
| failed | 执行失败 |
| cancelled | 已取消 |

---

## 4.7 获取任务进度（WebSocket）

**连接地址**

```
ws://localhost:18765/ws/compare/tasks/{task_id}/progress
```

**消息格式**

```json
{
  "type": "progress",
  "data": {
    "task_id": "task_001",
    "status": "running",
    "progress": {
      "total_tables": 10,
      "completed_tables": 3,
      "current_table": "t_order",
      "current_phase": "data",
      "percentage": 35.5,
      "elapsed_seconds": 120
    }
  }
}
```

**任务完成消息**

```json
{
  "type": "completed",
  "data": {
    "task_id": "task_001",
    "result_id": "result_001"
  }
}
```

**任务失败消息**

```json
{
  "type": "failed",
  "data": {
    "task_id": "task_001",
    "error_message": "数据库连接超时"
  }
}
```

---

# 5. 比对结果接口

## 5.1 获取比对结果

**请求**

```
GET /compare/results/{result_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| result_id | string | 是 | 结果ID |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "result_id": "result_001",
    "task_id": "task_001",
    "status": "completed",
    "source_db": {
      "id": "ds_001",
      "name": "生产环境-MySQL",
      "db_type": "mysql"
    },
    "target_db": {
      "id": "ds_002",
      "name": "测试环境-MySQL",
      "db_type": "mysql"
    },
    "start_time": "2026-03-20T10:00:00Z",
    "end_time": "2026-03-20T10:05:30Z",
    "duration_seconds": 330,
    "summary": {
      "total_tables": 10,
      "structure_match_tables": 8,
      "structure_diff_tables": 2,
      "data_match_tables": 7,
      "data_diff_tables": 3,
      "total_structure_diffs": 15,
      "total_data_diffs": 128
    }
  }
}
```

---

## 5.2 获取结构差异列表

**请求**

```
GET /compare/results/{result_id}/structure-diffs
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| table_name | string | 否 | 表名筛选 |
| diff_type | string | 否 | 差异类型筛选 |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "diff_001",
      "table_name": "t_user",
      "diff_type": "column_type_diff",
      "field_name": "age",
      "source_value": "int",
      "target_value": "bigint",
      "diff_detail": "字段 age 类型不同"
    },
    {
      "id": "diff_002",
      "table_name": "t_user",
      "diff_type": "column_missing",
      "field_name": "email",
      "source_value": "varchar(100)",
      "target_value": null,
      "diff_detail": "目标表缺少字段: email"
    }
  ],
  "page_info": {
    "page": 1,
    "page_size": 20,
    "total": 15,
    "total_pages": 1
  }
}
```

**差异类型说明**

| 类型 | 说明 |
|------|------|
| table_missing_in_target | 目标库缺表 |
| table_extra_in_target | 目标库多表 |
| column_missing | 目标表缺少字段 |
| column_extra | 目标表多余字段 |
| column_type_diff | 字段类型不同 |
| column_length_diff | 字段长度不同 |
| column_nullable_diff | 可空属性不同 |
| column_default_diff | 默认值不同 |
| index_diff | 索引不同 |
| constraint_diff | 约束不同 |
| comment_diff | 注释不同 |

---

## 5.3 获取数据差异列表

**请求**

```
GET /compare/results/{result_id}/data-diffs
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| table_name | string | 否 | 表名筛选 |
| diff_type | string | 否 | 差异类型筛选 |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "ddiff_001",
      "table_name": "t_user",
      "primary_key": {"id": 1001},
      "diff_type": "value_diff",
      "diff_columns": ["username", "age"],
      "source_values": {"username": "张三", "age": 25},
      "target_values": {"username": "张三丰", "age": 26}
    },
    {
      "id": "ddiff_002",
      "table_name": "t_user",
      "primary_key": {"id": 1002},
      "diff_type": "row_missing_in_target",
      "diff_columns": [],
      "source_values": {"id": 1002, "username": "李四", "age": 30},
      "target_values": null
    }
  ],
  "page_info": {
    "page": 1,
    "page_size": 20,
    "total": 128,
    "total_pages": 7
  }
}
```

**数据差异类型说明**

| 类型 | 说明 |
|------|------|
| row_count_diff | 行数不同 |
| row_missing_in_target | 目标库缺少该行 |
| row_extra_in_target | 目标库多余该行 |
| value_diff | 字段值不同 |
| null_diff | 空值差异 |

---

## 5.4 获取单表比对详情

**请求**

```
GET /compare/results/{result_id}/tables/{table_name}
```

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "table_name": "t_user",
    "structure_match": false,
    "data_match": false,
    "source_row_count": 10000,
    "target_row_count": 9998,
    "structure_diffs_count": 3,
    "data_diffs_count": 25,
    "compare_time_ms": 5230
  }
}
```

---

## 5.5 导出比对报告

**请求**

```
POST /compare/results/{result_id}/export
```

**请求体**

```json
{
  "format": "excel",
  "options": {
    "include_structure_diffs": true,
    "include_data_diffs": true,
    "max_data_diffs": 1000,
    "tables": null
  }
}
```

**请求参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| format | string | 是 | 导出格式：excel/html/txt |
| options.include_structure_diffs | boolean | 否 | 是否包含结构差异，默认true |
| options.include_data_diffs | boolean | 否 | 是否包含数据差异，默认true |
| options.max_data_diffs | integer | 否 | 数据差异最大导出数量，默认1000 |
| options.tables | array | 否 | 指定导出的表，null表示全部 |

**响应示例**

```json
{
  "code": 0,
  "message": "导出成功",
  "data": {
    "file_path": "/data/exports/report_20260320_100000.xlsx",
    "file_name": "比对报告_20260320_100000.xlsx",
    "file_size": 102400,
    "download_url": "/api/v1/files/download/report_20260320_100000.xlsx"
  }
}
```

---

## 5.6 下载导出文件

**请求**

```
GET /files/download/{file_name}
```

**响应**：文件流下载

---

# 6. 历史记录接口

## 6.1 获取历史记录列表

**请求**

```
GET /history
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_id | string | 否 | 源数据源ID筛选 |
| target_id | string | 否 | 目标数据源ID筛选 |
| status | string | 否 | 状态筛选 |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| keyword | string | 否 | 关键词搜索 |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "task_id": "task_001",
      "result_id": "result_001",
      "source_db": {
        "id": "ds_001",
        "name": "生产环境-MySQL"
      },
      "target_db": {
        "id": "ds_002",
        "name": "测试环境-MySQL"
      },
      "status": "completed",
      "table_count": 10,
      "has_diff": true,
      "structure_diffs_count": 5,
      "data_diffs_count": 20,
      "created_at": "2026-03-20T10:00:00Z",
      "duration_seconds": 330
    }
  ],
  "page_info": {
    "page": 1,
    "page_size": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

---

## 6.2 删除历史记录

**请求**

```
DELETE /history/{task_id}
```

---

## 6.3 批量删除历史记录

**请求**

```
POST /history/batch-delete
```

**请求体**

```json
{
  "task_ids": ["task_001", "task_002", "task_003"]
}
```

---

## 6.4 清理历史记录

**请求**

```
POST /history/cleanup
```

**请求体**

```json
{
  "before_date": "2026-01-01T00:00:00Z",
  "keep_count": 100
}
```

**说明**：保留最近 keep_count 条记录，删除 before_date 之前的记录

---

# 7. 忽略规则接口

## 7.1 获取忽略规则列表

**请求**

```
GET /settings/ignore-rules
```

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "rule_001",
      "name": "忽略更新时间字段",
      "rule_type": "column",
      "pattern": "*_time",
      "tables": null,
      "enabled": true,
      "created_at": "2026-03-01T00:00:00Z"
    },
    {
      "id": "rule_002",
      "name": "忽略大字段",
      "rule_type": "dataType",
      "pattern": "blob,clob,text",
      "tables": ["t_document", "t_attachment"],
      "enabled": true,
      "created_at": "2026-03-01T00:00:00Z"
    }
  ]
}
```

---

## 7.2 创建忽略规则

**请求**

```
POST /settings/ignore-rules
```

**请求体**

```json
{
  "name": "忽略创建时间字段",
  "rule_type": "column",
  "pattern": "create_time,created_at",
  "tables": null,
  "enabled": true
}
```

**规则类型说明**

| 类型 | 说明 | pattern示例 |
|------|------|-------------|
| column | 按字段名忽略 | `*_time`（支持通配符） |
| dataType | 按数据类型忽略 | `blob,clob,text` |
| diffType | 按差异类型忽略 | `comment_diff` |
| table | 按表名忽略 | `t_log*` |

---

## 7.3 更新忽略规则

**请求**

```
PUT /settings/ignore-rules/{id}
```

---

## 7.4 删除忽略规则

**请求**

```
DELETE /settings/ignore-rules/{id}
```

---

## 7.5 启用/禁用忽略规则

**请求**

```
PUT /settings/ignore-rules/{id}/toggle
```

**请求体**

```json
{
  "enabled": false
}
```

---

# 8. 比对模板接口

## 8.1 获取模板列表

**请求**

```
GET /settings/templates
```

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "tpl_001",
      "name": "生产到测试全量比对",
      "description": "用于生产环境到测试环境的全量数据比对",
      "config": {
        "source_id": "ds_001",
        "target_id": "ds_002",
        "table_selection": {
          "mode": "exclude",
          "tables": ["t_log", "t_temp"]
        },
        "options": {}
      },
      "created_at": "2026-03-01T00:00:00Z"
    }
  ]
}
```

---

## 8.2 创建模板

**请求**

```
POST /settings/templates
```

**请求体**

```json
{
  "name": "日常增量比对模板",
  "description": "用于日常增量数据比对",
  "config": {
    "source_id": "ds_001",
    "target_id": "ds_002",
    "table_selection": {
      "mode": "include",
      "tables": ["t_user", "t_order"]
    },
    "options": {
      "mode": "incremental",
      "data_options": {
        "skip_large_fields": true
      }
    }
  }
}
```

---

## 8.3 更新模板

**请求**

```
PUT /settings/templates/{id}
```

---

## 8.4 删除模板

**请求**

```
DELETE /settings/templates/{id}
```

---

## 8.5 从模板创建任务

**请求**

```
POST /settings/templates/{id}/create-task
```

**请求体（可选覆盖参数）**

```json
{
  "override": {
    "options": {
      "incremental_config": {
        "time_column": "update_time",
        "start_time": "2026-03-20T00:00:00Z"
      }
    }
  }
}
```

---

# 9. 系统设置接口

## 9.1 获取系统设置

**请求**

```
GET /settings/system
```

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "compare_thread_count": 4,
    "db_query_timeout": 60,
    "compare_timeout": 3600,
    "history_retention_days": 90,
    "history_max_count": 500,
    "default_page_size": 10000,
    "max_diff_display": 1000,
    "auto_cleanup_enabled": true
  }
}
```

---

## 9.2 更新系统设置

**请求**

```
PUT /settings/system
```

**请求体**

```json
{
  "compare_thread_count": 8,
  "history_retention_days": 60
}
```

---

## 9.3 导出配置

**请求**

```
POST /settings/export
```

**请求体**

```json
{
  "include_datasources": true,
  "include_templates": true,
  "include_rules": true
}
```

**响应示例**

```json
{
  "code": 0,
  "message": "导出成功",
  "data": {
    "file_path": "/data/exports/config_20260320.enc",
    "download_url": "/api/v1/files/download/config_20260320.enc"
  }
}
```

---

## 9.4 导入配置

**请求**

```
POST /settings/import
```

**请求体**：multipart/form-data

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 配置文件 |
| overwrite | boolean | 否 | 是否覆盖已有配置，默认false |

---

# 10. 健康检查接口

## 10.1 健康检查

**请求**

```
GET /health
```

**响应示例**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400
}
```

---

## 10.2 获取版本信息

**请求**

```
GET /version
```

**响应示例**

```json
{
  "version": "1.0.0",
  "build_time": "2026-03-20T00:00:00Z",
  "python_version": "3.11.7"
}
```
