-- Inceptor/Hive init dataset for UI integration tests
-- Target database: default
-- Strategy: baseline consistency + controlled diffs

USE default;

DROP TABLE IF EXISTS cmp_order_item;
DROP TABLE IF EXISTS cmp_order;
DROP TABLE IF EXISTS cmp_data_case;
DROP TABLE IF EXISTS cmp_struct_case;
DROP TABLE IF EXISTS cmp_no_pk_log;
DROP TABLE IF EXISTS cmp_user;
DROP TABLE IF EXISTS cmp_inceptor_only;

CREATE TABLE IF NOT EXISTS cmp_user (
  user_id INT,
  user_code STRING,
  user_name STRING,
  email STRING,
  user_status STRING,
  credit_score DECIMAL(10,2),
  created_at TIMESTAMP,
  remark STRING,
  CONSTRAINT pk_cmp_user PRIMARY KEY (user_id) DISABLE NOVALIDATE
)
COMMENT 'core users for compare tests'
STORED AS ORC;

CREATE TABLE IF NOT EXISTS cmp_order (
  order_id BIGINT,
  user_id INT,
  order_no STRING,
  amount DECIMAL(12,2),
  currency_code STRING,
  paid_flag INT,
  order_time TIMESTAMP,
  paid_time TIMESTAMP,
  note STRING,
  CONSTRAINT pk_cmp_order PRIMARY KEY (order_id) DISABLE NOVALIDATE
)
COMMENT 'orders for compare tests'
STORED AS ORC;

CREATE TABLE IF NOT EXISTS cmp_order_item (
  order_id BIGINT,
  line_no INT,
  sku_code STRING,
  qty INT,
  unit_price DECIMAL(10,2),
  discount_rate DECIMAL(5,4),
  ext_text STRING,
  CONSTRAINT pk_cmp_order_item PRIMARY KEY (order_id, line_no) DISABLE NOVALIDATE
)
COMMENT 'order item with composite key semantics'
STORED AS ORC;

CREATE TABLE IF NOT EXISTS cmp_data_case (
  id INT,
  text_value STRING,
  num_value DECIMAL(18,6),
  dt_value TIMESTAMP,
  nullable_flag STRING,
  whitespace_value STRING,
  case_value STRING,
  CONSTRAINT pk_cmp_data_case PRIMARY KEY (id) DISABLE NOVALIDATE
)
COMMENT 'rows for null/value/precision/case/trim checks'
STORED AS ORC;

CREATE TABLE IF NOT EXISTS cmp_struct_case (
  id BIGINT,
  code STRING,
  flag BIGINT,
  updated_at TIMESTAMP,
  extra_note STRING,
  CONSTRAINT pk_cmp_struct_case PRIMARY KEY (id) DISABLE NOVALIDATE
)
COMMENT 'intentionally different structure in inceptor'
STORED AS ORC;

CREATE TABLE IF NOT EXISTS cmp_no_pk_log (
  event_id INT,
  event_type STRING,
  payload STRING,
  created_at TIMESTAMP
)
COMMENT 'table without physical primary key'
STORED AS ORC;

CREATE TABLE IF NOT EXISTS cmp_inceptor_only (
  id INT,
  inceptor_feature STRING
)
COMMENT 'table only exists in inceptor'
STORED AS ORC;

-- Baseline consistency layer (cmp_user/cmp_order/cmp_order_item)
INSERT INTO TABLE cmp_user
SELECT 1, 'U1001', 'Alice', 'alice@example.com', 'A', CAST(98.50 AS DECIMAL(10,2)), CAST('2024-01-10 09:00:00' AS TIMESTAMP), 'core customer'
UNION ALL
SELECT 2, 'U1002', 'Bob', 'bob@example.com', 'A', CAST(77.00 AS DECIMAL(10,2)), CAST('2024-02-01 10:30:00' AS TIMESTAMP), 'has trailing spaces  '
UNION ALL
SELECT 3, 'U1003', 'Cathy', 'cathy@example.com', 'I', CAST(66.66 AS DECIMAL(10,2)), CAST('2024-03-20 12:20:00' AS TIMESTAMP), 'CaseTest'
UNION ALL
SELECT 4, 'U1004', 'David', NULL, 'A', CAST(0.00 AS DECIMAL(10,2)), CAST('2024-04-01 08:00:00' AS TIMESTAMP), NULL;

INSERT INTO TABLE cmp_order
SELECT 9001, 1, 'SO-202401-001', CAST(120.50 AS DECIMAL(12,2)), 'CNY', 1, CAST('2024-01-15 10:00:00' AS TIMESTAMP), CAST('2024-01-15 10:05:00' AS TIMESTAMP), 'paid'
UNION ALL
SELECT 9002, 1, 'SO-202401-002', CAST(88.00 AS DECIMAL(12,2)), 'CNY', 0, CAST('2024-01-16 11:00:00' AS TIMESTAMP), NULL, 'waiting payment'
UNION ALL
SELECT 9003, 2, 'SO-202402-003', CAST(35.90 AS DECIMAL(12,2)), 'USD', 1, CAST('2024-02-11 09:30:00' AS TIMESTAMP), CAST('2024-02-11 09:45:00' AS TIMESTAMP), NULL;

INSERT INTO TABLE cmp_order_item
SELECT 9001, 1, 'SKU-A-001', 2, CAST(30.00 AS DECIMAL(10,2)), CAST(0.1000 AS DECIMAL(5,4)), '{"channel":"app"}'
UNION ALL
SELECT 9001, 2, 'SKU-B-009', 1, CAST(60.50 AS DECIMAL(10,2)), CAST(0.0000 AS DECIMAL(5,4)), '{"channel":"app"}'
UNION ALL
SELECT 9002, 1, 'SKU-C-100', 4, CAST(22.00 AS DECIMAL(10,2)), CAST(0.0000 AS DECIMAL(5,4)), '{"channel":"web"}'
UNION ALL
SELECT 9003, 1, 'SKU-D-201', 1, CAST(35.90 AS DECIMAL(10,2)), CAST(0.0500 AS DECIMAL(5,4)), '{"channel":"store"}';

-- Controlled diffs layer (cmp_data_case)
-- id=1: NULL_DIFF (nullable_flag: NULL -> 'N')
-- id=2: VALUE_DIFF (whitespace_value: 'abc   ' -> 'abc', only visible when trim_whitespace=false)
-- id=3: VALUE_DIFF (case_value: 'MiXeD' -> 'mixed', only visible when ignore_case=false)
-- id=4: ROW_MISSING_IN_TARGET (source exists, target absent)
-- id=5: VALUE_DIFF (num precision)
-- id=6: ROW_EXTRA_IN_TARGET (target only)
INSERT INTO TABLE cmp_data_case
SELECT 1, 'same-row', CAST(100.123456 AS DECIMAL(18,6)), CAST('2024-01-01 10:00:00' AS TIMESTAMP), 'N', 'keep-space', 'CaseSensitive'
UNION ALL
SELECT 2, 'trim-check', CAST(9.900000 AS DECIMAL(18,6)), CAST('2024-01-02 10:00:00' AS TIMESTAMP), 'N', 'abc', 'abc'
UNION ALL
SELECT 3, 'case-check', CAST(1.000000 AS DECIMAL(18,6)), CAST('2024-01-03 10:00:00' AS TIMESTAMP), 'Y', 'A', 'mixed'
UNION ALL
SELECT 5, 'float-check', CAST(0.333334 AS DECIMAL(18,6)), CAST('2024-01-05 10:00:00' AS TIMESTAMP), 'Y', 'x', 'x'
UNION ALL
SELECT 6, 'target-extra', CAST(6.666666 AS DECIMAL(18,6)), CAST('2024-01-06 10:00:00' AS TIMESTAMP), 'N', 'extra', 'extra';

-- Intentionally different table structure for structure-diff checks
INSERT INTO TABLE cmp_struct_case
SELECT 1, 'S-1', 0, CAST('2024-01-01 01:00:00' AS TIMESTAMP), 'inceptor variant'
UNION ALL
SELECT 2, 'S-2', 1, CAST('2024-01-02 02:00:00' AS TIMESTAMP), NULL;

INSERT INTO TABLE cmp_no_pk_log
SELECT 1, 'sync_start', 'job-001', CAST('2024-01-01 00:00:00' AS TIMESTAMP)
UNION ALL
SELECT 1, 'sync_end', 'job-001', CAST('2024-01-01 00:01:00' AS TIMESTAMP);

INSERT INTO TABLE cmp_inceptor_only
SELECT 1, 'engine=inceptor';
