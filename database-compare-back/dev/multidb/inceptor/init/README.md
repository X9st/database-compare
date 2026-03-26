# Inceptor Init Template

Place your Inceptor/Hive initialization SQL/scripts in this directory.

Suggested object set (keep names aligned with other DBs):
- `cmp_user`
- `cmp_order`
- `cmp_order_item`
- `cmp_data_case`
- `cmp_struct_case`
- `cmp_no_pk_log`
- `cmp_inceptor_only`

Tip:
- Inceptor connector reads metadata through `SHOW TABLES` and `DESCRIBE`.
- Primary key/index/constraint semantics are limited in Hive-compatible engines.
