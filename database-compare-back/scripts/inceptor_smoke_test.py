#!/usr/bin/env python3
"""Inceptor connector smoke test for database-compare backend."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test Inceptor connector.")
    parser.add_argument("--host", required=True, help="Inceptor host")
    parser.add_argument("--port", type=int, default=10000, help="Inceptor port")
    parser.add_argument("--database", default="default", help="Inceptor database")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--password", default="", help="Password")
    parser.add_argument("--table", default="cmp_user", help="Table for schema/data checks")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        from app.core.connector import ConnectorFactory
    except Exception as exc:  # pragma: no cover
        print(f"[FAIL] import backend modules failed: {exc}")
        return 2

    connector = ConnectorFactory.create(
        db_type="inceptor",
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=args.password,
        charset="UTF-8",
        timeout=30,
    )

    print("[INFO] testing Inceptor connection...")
    test_result = connector.test_connection()
    print("[INFO] test_connection result:", json.dumps(test_result, ensure_ascii=False))
    if not test_result.get("success"):
        return 1

    print("[INFO] loading metadata/data...")
    connector.connect()
    try:
        tables = connector.get_tables()
        table_names = [t.name for t in tables]
        print(f"[INFO] tables count={len(table_names)}")
        print("[INFO] sample tables:", table_names[:20])

        cols = connector.get_columns(args.table)
        pks = connector.get_primary_keys(args.table)
        cnt = connector.get_row_count(args.table)
        rows = connector.fetch_data(args.table, limit=3)

        print(f"[INFO] table={args.table} columns={len(cols)} pks={pks} row_count={cnt}")
        print("[INFO] first rows:", json.dumps(rows, ensure_ascii=False, default=str))
    finally:
        connector.disconnect()

    print("[PASS] Inceptor connector smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
