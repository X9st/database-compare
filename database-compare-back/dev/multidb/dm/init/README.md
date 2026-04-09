# DM Init Scripts (MySQL <-> DM Integration)

This directory now provides a runnable, repeatable DM seed for the Windows integration plan.

## Files

- `00-create-qa-schema.sql`
  - Run as `SYSDBA`
  - Creates/updates `QA_SCHEMA` and grants minimal object-creation privileges
- `01-schema-data.sql`
  - Run as `SYSDBA` (or privileged user)
  - Idempotent schema/data bootstrap for compare tests
- `02-verify.sql`
  - Row-count and controlled-diff verification SQL

## Object Set

- `CMP_USER`
- `CMP_ORDER`
- `CMP_ORDER_ITEM`
- `CMP_DATA_CASE`
- `CMP_STRUCT_CASE`
- `CMP_NO_PK_LOG`
- `CMP_DM_ONLY`

## Execution Order

```sql
-- in disql
@00-create-qa-schema.sql
@01-schema-data.sql
@02-verify.sql
```

You can also run these files from the backend venv:

```powershell
cd d:\database-compare\database-compare-back
.\venv\Scripts\python.exe scripts\dm_exec_sql_file.py `
  --host 39.105.124.246 `
  --port 5236 `
  --username SYSDBA `
  --password AAAaaa11 `
  --sql-file dev\multidb\dm\init\00-create-qa-schema.sql `
  --sql-file dev\multidb\dm\init\01-schema-data.sql `
  --sql-file dev\multidb\dm\init\02-verify.sql
```

## Notes

- Object names stay uppercase to align with `DMConnector` behavior.
- `CMP_DATA_CASE` includes controlled data differences used by TC03/TC04.
- `CMP_STRUCT_CASE` intentionally differs from MySQL for structure-diff validation.
- `CMP_NO_PK_LOG` has no PK for business-primary-key test flow.
