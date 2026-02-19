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
  BACKUP_ROOT="$DATA_DIR/backups/storage-ab"
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -n "$LABEL" ]]; then
  BACKUP_DIR="$BACKUP_ROOT/$LABEL"
else
  BACKUP_DIR="$BACKUP_ROOT/backup-$TS"
fi

FILES_DIR="$DATA_DIR/files"
TRS_DB="$DATA_DIR/tool_results.db"

mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/files"
mkdir -p "$BACKUP_DIR/db"

if [[ -d "$FILES_DIR" ]]; then
  cp -R "$FILES_DIR/." "$BACKUP_DIR/files/"
fi

if [[ -f "$TRS_DB" ]]; then
  cp "$TRS_DB" "$BACKUP_DIR/db/tool_results.db"
fi
if [[ -f "$TRS_DB-wal" ]]; then
  cp "$TRS_DB-wal" "$BACKUP_DIR/db/tool_results.db-wal"
fi
if [[ -f "$TRS_DB-shm" ]]; then
  cp "$TRS_DB-shm" "$BACKUP_DIR/db/tool_results.db-shm"
fi

python - "$BACKUP_DIR" <<'PY'
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

backup_dir = Path(sys.argv[1])
files_dir = backup_dir / "files"
db_path = backup_dir / "db" / "tool_results.db"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

file_count = 0
for _, _, files in os.walk(files_dir):
    file_count += len(files)

db_row_count = None
db_sha256 = None
if db_path.exists():
    db_sha256 = sha256(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute("SELECT COUNT(1) FROM tool_results").fetchone()
    db_row_count = int(row[0]) if row else 0

manifest = {
    "generated_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    "backup_dir": str(backup_dir),
    "files": {"count": file_count},
    "tool_results_db": {
        "exists": db_path.exists(),
        "row_count": db_row_count,
        "sha256": db_sha256,
    },
}

(backup_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
PY

echo "BACKUP_DIR=$BACKUP_DIR"
echo "MANIFEST=$BACKUP_DIR/manifest.json"
