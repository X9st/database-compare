#!/usr/bin/env python3
"""API probe for MySQL + DM datasource smoke checks."""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class ProbeContext:
    base_url: str
    client: httpx.Client
    created_ds_ids: List[str]
    keep: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe /datasources endpoints for MySQL and DM.")
    parser.add_argument("--base-url", default="http://localhost:18765", help="Backend base URL")
    parser.add_argument("--mysql-host", default="localhost")
    parser.add_argument("--mysql-port", type=int, default=3306)
    parser.add_argument("--mysql-user", default="root")
    parser.add_argument("--mysql-password", default="root")
    parser.add_argument("--mysql-database", default="source_db")
    parser.add_argument("--dm-host", required=True)
    parser.add_argument("--dm-port", type=int, default=5236)
    parser.add_argument("--dm-user", required=True)
    parser.add_argument("--dm-password", required=True)
    parser.add_argument("--dm-database", default="DM8")
    parser.add_argument("--dm-schema", default="QA_SCHEMA")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--keep", action="store_true", help="Keep created datasource records")
    return parser.parse_args()


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _extract_data(payload: Dict[str, Any]) -> Any:
    if not isinstance(payload, dict):
        return payload
    return payload.get("data", payload)


def _request_json(ctx: ProbeContext, method: str, path: str, **kwargs) -> Dict[str, Any]:
    url = _url(ctx.base_url, path)
    resp = ctx.client.request(method, url, **kwargs)
    resp.raise_for_status()
    body = resp.json()
    if not isinstance(body, dict):
        raise RuntimeError(f"Unexpected response shape for {path}: {body}")
    return body


def _print(title: str, value: Any) -> None:
    print(f"[INFO] {title}: {json.dumps(value, ensure_ascii=False, default=str)}")


def probe_direct_test(ctx: ProbeContext, payload: Dict[str, Any], label: str) -> None:
    body = _request_json(ctx, "POST", "/api/v1/datasources/test", json=payload)
    data = _extract_data(body)
    _print(f"{label} direct test", data)
    if not data.get("success"):
        raise RuntimeError(f"{label} direct test failed: {data}")


def create_datasource(ctx: ProbeContext, payload: Dict[str, Any], label: str) -> str:
    body = _request_json(ctx, "POST", "/api/v1/datasources", json=payload)
    data = _extract_data(body)
    ds_id = str(data.get("id") or "")
    if not ds_id:
        raise RuntimeError(f"{label} create datasource got empty id: {data}")
    ctx.created_ds_ids.append(ds_id)
    _print(f"{label} created datasource", {"id": ds_id, "name": data.get("name")})
    return ds_id


def test_saved_datasource(ctx: ProbeContext, ds_id: str, label: str) -> None:
    body = _request_json(ctx, "POST", f"/api/v1/datasources/{ds_id}/test")
    data = _extract_data(body)
    _print(f"{label} saved test", data)
    if not data.get("success"):
        raise RuntimeError(f"{label} saved datasource test failed: {data}")


def list_tables(ctx: ProbeContext, ds_id: str, label: str) -> None:
    body = _request_json(ctx, "GET", f"/api/v1/datasources/{ds_id}/tables")
    data = _extract_data(body)
    if not isinstance(data, list):
        raise RuntimeError(f"{label} tables response is not a list: {data}")
    _print(f"{label} tables summary", {"count": len(data), "sample": [t.get('name') for t in data[:10]]})
    if len(data) == 0:
        raise RuntimeError(f"{label} tables list is empty.")


def cleanup_datasources(ctx: ProbeContext) -> None:
    if ctx.keep:
        _print("cleanup skipped", {"created_ds_ids": ctx.created_ds_ids})
        return
    for ds_id in reversed(ctx.created_ds_ids):
        try:
            _request_json(ctx, "DELETE", f"/api/v1/datasources/{ds_id}")
            _print("cleanup deleted datasource", ds_id)
        except Exception as exc:
            _print("cleanup delete failed", {"id": ds_id, "error": str(exc)})


def main() -> int:
    args = parse_args()
    run_id = uuid.uuid4().hex[:8]
    timeout = httpx.Timeout(args.timeout)
    created: List[str] = []

    with httpx.Client(timeout=timeout) as client:
        ctx = ProbeContext(
            base_url=args.base_url,
            client=client,
            created_ds_ids=created,
            keep=bool(args.keep),
        )
        try:
            mysql_test_payload = {
                "db_type": "mysql",
                "host": args.mysql_host,
                "port": args.mysql_port,
                "database": args.mysql_database,
                "username": args.mysql_user,
                "password": args.mysql_password,
                "charset": "UTF-8",
                "timeout": args.timeout,
            }
            dm_test_payload = {
                "db_type": "dm",
                "host": args.dm_host,
                "port": args.dm_port,
                "database": args.dm_database,
                "schema": args.dm_schema,
                "username": args.dm_user,
                "password": args.dm_password,
                "charset": "UTF-8",
                "timeout": args.timeout,
            }

            probe_direct_test(ctx, mysql_test_payload, "mysql")
            probe_direct_test(ctx, dm_test_payload, "dm")

            mysql_create_payload = {
                "name": f"qa-mysql-{run_id}",
                **mysql_test_payload,
            }
            dm_create_payload = {
                "name": f"qa-dm-{run_id}",
                **dm_test_payload,
            }

            mysql_id = create_datasource(ctx, mysql_create_payload, "mysql")
            dm_id = create_datasource(ctx, dm_create_payload, "dm")

            test_saved_datasource(ctx, mysql_id, "mysql")
            test_saved_datasource(ctx, dm_id, "dm")

            list_tables(ctx, mysql_id, "mysql")
            list_tables(ctx, dm_id, "dm")

            _print("probe result", {"ok": True, "run_id": run_id})
            return 0
        except Exception as exc:
            _print("probe result", {"ok": False, "error": str(exc), "run_id": run_id})
            return 1
        finally:
            cleanup_datasources(ctx)


if __name__ == "__main__":
    raise SystemExit(main())

