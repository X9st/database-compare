#!/usr/bin/env bash
set -euo pipefail

SQLCMD=""
SQLCMD_TLS_FLAG=()
if [ -x /opt/mssql-tools18/bin/sqlcmd ]; then
  SQLCMD="/opt/mssql-tools18/bin/sqlcmd"
  SQLCMD_TLS_FLAG=(-C)
elif [ -x /opt/mssql-tools/bin/sqlcmd ]; then
  SQLCMD="/opt/mssql-tools/bin/sqlcmd"
else
  echo "sqlcmd not found in container"
  exit 1
fi

echo "[sqlserver-init] waiting for sqlserver..."
for i in $(seq 1 90); do
  if "$SQLCMD" -S sqlserver -U sa -P "$MSSQL_SA_PASSWORD" "${SQLCMD_TLS_FLAG[@]}" -Q "SELECT 1" >/dev/null 2>&1; then
    echo "[sqlserver-init] sqlserver is ready"
    break
  fi
  sleep 2
  if [ "$i" -eq 90 ]; then
    echo "[sqlserver-init] timeout while waiting for sqlserver"
    exit 1
  fi
done

echo "[sqlserver-init] applying /init/01-schema-data.sql"
"$SQLCMD" -S sqlserver -U sa -P "$MSSQL_SA_PASSWORD" "${SQLCMD_TLS_FLAG[@]}" -b -i /init/01-schema-data.sql

echo "[sqlserver-init] done"
