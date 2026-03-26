# DM Init Template

Place your DM initialization SQL/scripts in this directory.

Suggested object set (keep names aligned with other DBs):
- `cmp_user`
- `cmp_order`
- `cmp_order_item`
- `cmp_data_case`
- `cmp_struct_case`
- `cmp_no_pk_log`
- `cmp_dm_only`

Tip:
- Use uppercase object names to match the current DM connector behavior.
- Keep explicit index/constraint names for cleaner structure diff output.
