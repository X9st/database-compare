#!/usr/bin/env python3
"""Execute DM SQL files with simple block-aware parsing."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import dmPython


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute SQL files against DM database.")
    parser.add_argument("--host", required=True, help="DM host")
    parser.add_argument("--port", type=int, default=5236, help="DM port")
    parser.add_argument("--username", required=True, help="DM username")
    parser.add_argument("--password", required=True, help="DM password")
    parser.add_argument("--sql-file", action="append", required=True, help="SQL file path, can be repeated")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop execution when any statement fails")
    return parser.parse_args()


def split_statements(sql_text: str) -> List[str]:
    statements: List[str] = []
    buffer: List[str] = []
    in_block = False

    for raw_line in sql_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue

        if not buffer and stripped.upper().startswith(("BEGIN", "DECLARE")):
            in_block = True

        if stripped == "/" and in_block:
            stmt = "\n".join(buffer).strip()
            if stmt:
                statements.append(stmt)
            buffer = []
            in_block = False
            continue

        buffer.append(line)

        if not in_block and stripped.endswith(";"):
            stmt = "\n".join(buffer).strip()
            if stmt.endswith(";"):
                stmt = stmt[:-1].rstrip()
            if stmt:
                statements.append(stmt)
            buffer = []

    if buffer:
        stmt = "\n".join(buffer).strip()
        if stmt:
            statements.append(stmt)

    return statements


def main() -> int:
    args = parse_args()
    dsn = f"{args.username}/{args.password}@{args.host}:{args.port}"
    conn = dmPython.connect(dsn)
    try:
        for sql_file in args.sql_file:
            path = Path(sql_file).resolve()
            text = path.read_text(encoding="utf-8")
            statements = split_statements(text)
            print(f"[INFO] file={path} statements={len(statements)}")
            for idx, stmt in enumerate(statements, start=1):
                cur = conn.cursor()
                try:
                    cur.execute(stmt)
                    if idx % 20 == 0:
                        print(f"[INFO] {path.name}: executed {idx}/{len(statements)}")
                except Exception as exc:
                    print(f"[ERROR] {path.name} statement#{idx} failed: {exc}")
                    if args.stop_on_error:
                        return 1
                finally:
                    cur.close()
            conn.commit()
            print(f"[INFO] file done: {path.name}")
    finally:
        conn.close()
    print("[PASS] SQL files execution completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

