#!/usr/bin/env bash
set -euo pipefail

ORACLE_APP_USER=${ORACLE_APP_USER:-qa_compare}
ORACLE_APP_PASSWORD=${ORACLE_APP_PASSWORD:-OracleApp_123456}
ORACLE_SERVICE=${ORACLE_SERVICE:-FREEPDB1}
CONNECT_STRING="${ORACLE_APP_USER}/${ORACLE_APP_PASSWORD}@oracle:1521/${ORACLE_SERVICE}"

echo "[oracle-init] waiting for oracle..."
for i in $(seq 1 120); do
  if echo "SELECT 1 FROM dual;" | sqlplus -s "$CONNECT_STRING" >/dev/null 2>&1; then
    echo "[oracle-init] oracle is ready"
    break
  fi
  sleep 3
  if [ "$i" -eq 120 ]; then
    echo "[oracle-init] timeout while waiting for oracle"
    exit 1
  fi
done

echo "[oracle-init] applying /init/01-schema-data.sql"
sqlplus -s "$CONNECT_STRING" @/init/01-schema-data.sql

echo "[oracle-init] done"
