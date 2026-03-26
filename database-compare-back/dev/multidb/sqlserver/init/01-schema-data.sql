IF DB_ID(N'qa_compare_mssql') IS NULL
BEGIN
  CREATE DATABASE qa_compare_mssql;
END
GO

USE qa_compare_mssql;
GO

IF OBJECT_ID(N'dbo.cmp_order_item', N'U') IS NOT NULL DROP TABLE dbo.cmp_order_item;
IF OBJECT_ID(N'dbo.cmp_order', N'U') IS NOT NULL DROP TABLE dbo.cmp_order;
IF OBJECT_ID(N'dbo.cmp_data_case', N'U') IS NOT NULL DROP TABLE dbo.cmp_data_case;
IF OBJECT_ID(N'dbo.cmp_struct_case', N'U') IS NOT NULL DROP TABLE dbo.cmp_struct_case;
IF OBJECT_ID(N'dbo.cmp_no_pk_log', N'U') IS NOT NULL DROP TABLE dbo.cmp_no_pk_log;
IF OBJECT_ID(N'dbo.cmp_user', N'U') IS NOT NULL DROP TABLE dbo.cmp_user;
IF OBJECT_ID(N'dbo.cmp_mssql_only', N'U') IS NOT NULL DROP TABLE dbo.cmp_mssql_only;
GO

CREATE TABLE dbo.cmp_user (
  user_id INT NOT NULL,
  user_code VARCHAR(20) NOT NULL,
  user_name VARCHAR(50) NOT NULL,
  email VARCHAR(100) NULL,
  user_status CHAR(1) NOT NULL CONSTRAINT df_cmp_user_status DEFAULT 'A',
  credit_score DECIMAL(10,2) NOT NULL CONSTRAINT df_cmp_user_score DEFAULT 0,
  created_at DATETIME2 NOT NULL CONSTRAINT df_cmp_user_created DEFAULT SYSDATETIME(),
  remark VARCHAR(200) NULL,
  CONSTRAINT pk_cmp_user PRIMARY KEY (user_id),
  CONSTRAINT uq_cmp_user_code UNIQUE (user_code)
);
GO

CREATE INDEX idx_cmp_user_status ON dbo.cmp_user(user_status);
GO

CREATE TABLE dbo.cmp_order (
  order_id BIGINT NOT NULL,
  user_id INT NOT NULL,
  order_no VARCHAR(30) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  currency_code CHAR(3) NOT NULL CONSTRAINT df_cmp_order_ccy DEFAULT 'CNY',
  paid_flag INT NOT NULL CONSTRAINT df_cmp_order_paid DEFAULT 0,
  order_time DATETIME2 NOT NULL,
  paid_time DATETIME2 NULL,
  note VARCHAR(200) NULL,
  CONSTRAINT pk_cmp_order PRIMARY KEY (order_id),
  CONSTRAINT uq_cmp_order_no UNIQUE (order_no),
  CONSTRAINT fk_cmp_order_user FOREIGN KEY (user_id) REFERENCES dbo.cmp_user(user_id)
);
GO

CREATE INDEX idx_cmp_order_user_time ON dbo.cmp_order(user_id, order_time);
GO

CREATE TABLE dbo.cmp_order_item (
  order_id BIGINT NOT NULL,
  line_no INT NOT NULL,
  sku_code VARCHAR(30) NOT NULL,
  qty INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  discount_rate DECIMAL(5,4) NOT NULL CONSTRAINT df_cmp_item_discount DEFAULT 0,
  ext_text VARCHAR(200) NULL,
  CONSTRAINT pk_cmp_order_item PRIMARY KEY (order_id, line_no),
  CONSTRAINT fk_cmp_item_order FOREIGN KEY (order_id) REFERENCES dbo.cmp_order(order_id)
);
GO

CREATE TABLE dbo.cmp_data_case (
  id INT NOT NULL,
  text_value VARCHAR(50) NULL,
  num_value DECIMAL(18,6) NULL,
  dt_value DATETIME2 NULL,
  nullable_flag VARCHAR(10) NULL,
  whitespace_value VARCHAR(50) NULL,
  case_value VARCHAR(50) NULL,
  CONSTRAINT pk_cmp_data_case PRIMARY KEY (id)
);
GO

CREATE TABLE dbo.cmp_struct_case (
  id INT NOT NULL,
  code VARCHAR(20) NOT NULL,
  description VARCHAR(120) NOT NULL CONSTRAINT df_cmp_struct_desc DEFAULT '',
  flag INT NOT NULL CONSTRAINT df_cmp_struct_flag DEFAULT 0,
  updated_at DATETIME2 NULL,
  CONSTRAINT pk_cmp_struct_case PRIMARY KEY (id)
);
GO

CREATE INDEX idx_cmp_struct_code ON dbo.cmp_struct_case(code);
GO

CREATE TABLE dbo.cmp_no_pk_log (
  event_id INT NOT NULL,
  event_type VARCHAR(30) NOT NULL,
  payload VARCHAR(100) NULL,
  created_at DATETIME2 NOT NULL
);
GO

CREATE TABLE dbo.cmp_mssql_only (
  id INT NOT NULL,
  mssql_feature VARCHAR(40) NOT NULL,
  CONSTRAINT pk_cmp_mssql_only PRIMARY KEY (id)
);
GO

INSERT INTO dbo.cmp_user (user_id, user_code, user_name, email, user_status, credit_score, created_at, remark) VALUES
(1, 'U1001', 'Alice', 'alice@example.com', 'A', 98.50, '2024-01-10 09:00:00', 'core customer'),
(2, 'U1002', 'Bob', 'bob@example.com', 'A', 77.00, '2024-02-01 10:30:00', 'has trailing spaces  '),
(3, 'U1003', 'Cathy', 'cathy@example.com', 'I', 66.66, '2024-03-20 12:20:00', 'CaseTest'),
(4, 'U1004', 'David', NULL, 'A', 0.00, '2024-04-01 08:00:00', NULL);

INSERT INTO dbo.cmp_order (order_id, user_id, order_no, amount, currency_code, paid_flag, order_time, paid_time, note) VALUES
(9001, 1, 'SO-202401-001', 120.50, 'CNY', 1, '2024-01-15 10:00:00', '2024-01-15 10:05:00', 'paid'),
(9002, 1, 'SO-202401-002', 88.00, 'CNY', 0, '2024-01-16 11:00:00', NULL, 'waiting payment'),
(9003, 2, 'SO-202402-003', 35.90, 'USD', 1, '2024-02-11 09:30:00', '2024-02-11 09:45:00', NULL);

INSERT INTO dbo.cmp_order_item (order_id, line_no, sku_code, qty, unit_price, discount_rate, ext_text) VALUES
(9001, 1, 'SKU-A-001', 2, 30.00, 0.1000, '{"channel":"app"}'),
(9001, 2, 'SKU-B-009', 1, 60.50, 0.0000, '{"channel":"app"}'),
(9002, 1, 'SKU-C-100', 4, 22.00, 0.0000, '{"channel":"web"}'),
(9003, 1, 'SKU-D-201', 1, 35.90, 0.0500, '{"channel":"store"}');

INSERT INTO dbo.cmp_data_case (id, text_value, num_value, dt_value, nullable_flag, whitespace_value, case_value) VALUES
(1, 'same-row', 100.123456, '2024-01-01 10:00:00', NULL, 'keep-space', 'CaseSensitive'),
(2, 'trim-check', 9.900000, '2024-01-02 10:00:00', 'N', 'abc  ', 'abc'),
(3, 'case-check', 1.000000, '2024-01-03 10:00:00', 'Y', 'A', 'MIXED'),
(4, NULL, 42.420000, NULL, NULL, NULL, NULL),
(5, 'float-check', 0.333330, '2024-01-05 10:00:00', 'Y', 'x', 'x');

INSERT INTO dbo.cmp_struct_case (id, code, description, flag, updated_at) VALUES
(1, 'S-1', 'mssql variant', 0, '2024-01-01 01:00:00'),
(2, 'S-2', '', 1, NULL);

INSERT INTO dbo.cmp_no_pk_log (event_id, event_type, payload, created_at) VALUES
(1, 'sync_start', 'job-001', '2024-01-01 00:00:00'),
(1, 'sync_end', 'job-001', '2024-01-01 00:01:00');

INSERT INTO dbo.cmp_mssql_only (id, mssql_feature) VALUES
(1, 'dbo schema default');
GO
