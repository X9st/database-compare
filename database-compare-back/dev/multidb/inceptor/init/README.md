# Inceptor Init Scripts

This directory contains runnable Inceptor/Hive initialization scripts for UI integration tests.

## Included script

- `01-schema-data.sql`

It initializes the following object set:

- `cmp_user`
- `cmp_order`
- `cmp_order_item`
- `cmp_data_case`
- `cmp_struct_case`
- `cmp_no_pk_log`
- `cmp_inceptor_only`

## Execution example

```bash
docker exec dbcmp-inceptor bash -lc "sudo -u hive /usr/lib/transwarp/scripts/beeline \
  -u 'jdbc:hive2://127.0.0.1:10000/default' \
  -n <inceptor_user> -p '<inceptor_password>' \
  -f /init/01-schema-data.sql"
```

## Notes

- The script is idempotent (`DROP TABLE IF EXISTS` + `CREATE TABLE`).
- Data strategy is baseline consistency plus controlled diffs.
- Core tables declare logical primary keys via `PRIMARY KEY ... DISABLE NOVALIDATE` (except `cmp_no_pk_log`).
- Inceptor connector reads metadata via `SHOW TABLES` and `DESCRIBE`.
- Primary key/index/constraint semantics are limited in Hive-compatible engines.
