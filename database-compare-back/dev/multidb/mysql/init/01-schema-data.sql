SET NAMES utf8mb4;
SET time_zone = '+08:00';

DROP TABLE IF EXISTS cmp_order_item;
DROP TABLE IF EXISTS cmp_order;
DROP TABLE IF EXISTS cmp_data_case;
DROP TABLE IF EXISTS cmp_struct_case;
DROP TABLE IF EXISTS cmp_no_pk_log;
DROP TABLE IF EXISTS cmp_user;
DROP TABLE IF EXISTS cmp_mysql_only;

CREATE TABLE cmp_user (
  user_id INT NOT NULL,
  user_code VARCHAR(20) NOT NULL,
  user_name VARCHAR(50) NOT NULL,
  email VARCHAR(100) NULL,
  user_status CHAR(1) NOT NULL DEFAULT 'A',
  credit_score DECIMAL(10,2) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  remark VARCHAR(200) NULL,
  PRIMARY KEY (user_id),
  CONSTRAINT uq_cmp_user_code UNIQUE (user_code)
) COMMENT='core users for compare tests';

CREATE INDEX idx_cmp_user_status ON cmp_user(user_status);

CREATE TABLE cmp_order (
  order_id BIGINT NOT NULL,
  user_id INT NOT NULL,
  order_no VARCHAR(30) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  currency_code CHAR(3) NOT NULL DEFAULT 'CNY',
  paid_flag TINYINT NOT NULL DEFAULT 0,
  order_time DATETIME NOT NULL,
  paid_time DATETIME NULL,
  note VARCHAR(200) NULL,
  PRIMARY KEY (order_id),
  CONSTRAINT uq_cmp_order_no UNIQUE (order_no),
  CONSTRAINT fk_cmp_order_user FOREIGN KEY (user_id) REFERENCES cmp_user(user_id)
) COMMENT='orders for compare tests';

CREATE INDEX idx_cmp_order_user_time ON cmp_order(user_id, order_time);

CREATE TABLE cmp_order_item (
  order_id BIGINT NOT NULL,
  line_no INT NOT NULL,
  sku_code VARCHAR(30) NOT NULL,
  qty INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  discount_rate DECIMAL(5,4) NOT NULL DEFAULT 0,
  ext_text VARCHAR(200) NULL,
  PRIMARY KEY (order_id, line_no),
  CONSTRAINT fk_cmp_item_order FOREIGN KEY (order_id) REFERENCES cmp_order(order_id)
) COMMENT='order item with composite key';

CREATE TABLE cmp_data_case (
  id INT NOT NULL,
  text_value VARCHAR(50) NULL,
  num_value DECIMAL(18,6) NULL,
  dt_value DATETIME NULL,
  nullable_flag VARCHAR(10) NULL,
  whitespace_value VARCHAR(50) NULL,
  case_value VARCHAR(50) NULL,
  PRIMARY KEY (id)
) COMMENT='rows for null/value/precision/case/trim checks';

CREATE TABLE cmp_struct_case (
  id INT NOT NULL,
  code VARCHAR(20) NOT NULL,
  description VARCHAR(120) NULL,
  flag INT NOT NULL DEFAULT 0,
  updated_at DATETIME NULL,
  PRIMARY KEY (id),
  CONSTRAINT uq_cmp_struct_code UNIQUE (code)
) COMMENT='this table is intentionally different by database';

CREATE TABLE cmp_no_pk_log (
  event_id INT NOT NULL,
  event_type VARCHAR(30) NOT NULL,
  payload VARCHAR(100) NULL,
  created_at DATETIME NOT NULL
) COMMENT='table without primary key for behavior validation';

CREATE TABLE cmp_mysql_only (
  id INT NOT NULL,
  mysql_feature VARCHAR(40) NOT NULL,
  PRIMARY KEY (id)
) COMMENT='table only exists in mysql';

INSERT INTO cmp_user (user_id, user_code, user_name, email, user_status, credit_score, created_at, remark) VALUES
(1, 'U1001', 'Alice', 'alice@example.com', 'A', 98.50, '2024-01-10 09:00:00', 'core customer'),
(2, 'U1002', 'Bob', 'bob@example.com', 'A', 77.00, '2024-02-01 10:30:00', 'has trailing spaces  '),
(3, 'U1003', 'Cathy', 'cathy@example.com', 'I', 66.66, '2024-03-20 12:20:00', 'CaseTest'),
(4, 'U1004', 'David', NULL, 'A', 0.00, '2024-04-01 08:00:00', NULL);

INSERT INTO cmp_order (order_id, user_id, order_no, amount, currency_code, paid_flag, order_time, paid_time, note) VALUES
(9001, 1, 'SO-202401-001', 120.50, 'CNY', 1, '2024-01-15 10:00:00', '2024-01-15 10:05:00', 'paid'),
(9002, 1, 'SO-202401-002', 88.00, 'CNY', 0, '2024-01-16 11:00:00', NULL, 'waiting payment'),
(9003, 2, 'SO-202402-003', 35.90, 'USD', 1, '2024-02-11 09:30:00', '2024-02-11 09:45:00', NULL);

INSERT INTO cmp_order_item (order_id, line_no, sku_code, qty, unit_price, discount_rate, ext_text) VALUES
(9001, 1, 'SKU-A-001', 2, 30.00, 0.1000, '{"channel":"app"}'),
(9001, 2, 'SKU-B-009', 1, 60.50, 0.0000, '{"channel":"app"}'),
(9002, 1, 'SKU-C-100', 4, 22.00, 0.0000, '{"channel":"web"}'),
(9003, 1, 'SKU-D-201', 1, 35.90, 0.0500, '{"channel":"store"}');

INSERT INTO cmp_data_case (id, text_value, num_value, dt_value, nullable_flag, whitespace_value, case_value) VALUES
(1, 'same-row', 100.123456, '2024-01-01 10:00:00', NULL, 'keep-space', 'CaseSensitive'),
(2, 'trim-check', 9.900000, '2024-01-02 10:00:00', 'N', 'abc   ', 'abc'),
(3, 'case-check', 1.000000, '2024-01-03 10:00:00', 'Y', 'A', 'MiXeD'),
(4, NULL, 42.420000, NULL, NULL, NULL, NULL),
(5, 'float-check', 0.333333, '2024-01-05 10:00:00', 'Y', 'x', 'x');

INSERT INTO cmp_struct_case (id, code, description, flag, updated_at) VALUES
(1, 'S-1', 'mysql base', 0, '2024-01-01 01:00:00'),
(2, 'S-2', NULL, 1, NULL);

INSERT INTO cmp_no_pk_log (event_id, event_type, payload, created_at) VALUES
(1, 'sync_start', 'job-001', '2024-01-01 00:00:00'),
(1, 'sync_end', 'job-001', '2024-01-01 00:01:00');

INSERT INTO cmp_mysql_only (id, mysql_feature) VALUES
(1, 'engine=innodb');
