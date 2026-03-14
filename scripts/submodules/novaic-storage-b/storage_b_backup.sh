#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/.novaic}"
BACKUP_ROOT=""
LABEL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --data-dir)
      DATA_DIR="$2"
      shift 2
      ;;
    --backup-root)
      BACKUP_ROOT="$2"
      shift 2
      ;;
    --label)
      LABEL="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [--data-dir DIR] [--backup-root DIR] [--label NAME]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$BACKUP_ROOT" ]]; then
  BACKUP_ROOT="$DATA_DIR/backups/storage-b"
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -n "$LABEL" ]]; then
  BACKUP_DIR="$BACKUP_ROOT/$LABEL"
else
  BACKUP_DIR="$BACKUP_ROOT/backup-$TS"
fi

mkdir -p "$BACKUP_DIR/db"
DB_PATH="$DATA_DIR/tool_results.db"

if [[ -f "$DB_PATH" ]]; then
  cp "$DB_PATH" "$BACKUP_DIR/db/tool_results.db"
fi
if [[ -f "$DB_PATH-wal" ]]; then
  cp "$DB_PATH-wal" "$BACKUP_DIR/db/tool_results.db-wal"
fi
if [[ -f "$DB_PATH-shm" ]]; then
  cp "$DB_PATH-shm" "$BACKUP_DIR/db/tool_results.db-shm"
fi

python - "$BACKUP_DIR" <<'PY'
import json
import sqlite3
import sys
from pathlib import Path

backup_dir = Path(sys.argv[1])
db_path = backup_dir / "db" / "tool_results.db"
row_count = None
if db_path.exists():
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute("SELECT COUNT(1) FROM tool_results").fetchone()
    row_count = int(row[0]) if row else 0

manifest = {
    "domain": "storage-b",
    "generated_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    "backup_dir": str(backup_dir),
    "tool_results_db": {"exists": db_path.exists(), "row_count": row_count},
}
(backup_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
PY

echo "STORAGE_B_BACKUP_OK=true"
echo "BACKUP_DIR=$BACKUP_DIR"
echo "MANIFEST=$BACKUP_DIR/manifest.json"
