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
  BACKUP_ROOT="$DATA_DIR/backups/storage-a"
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -n "$LABEL" ]]; then
  BACKUP_DIR="$BACKUP_ROOT/$LABEL"
else
  BACKUP_DIR="$BACKUP_ROOT/backup-$TS"
fi

FILES_DIR="$DATA_DIR/files"
mkdir -p "$BACKUP_DIR/files"

if [[ -d "$FILES_DIR" ]]; then
  cp -R "$FILES_DIR/." "$BACKUP_DIR/files/"
fi

python - "$BACKUP_DIR" <<'PY'
import json
import os
import sys
from pathlib import Path

backup_dir = Path(sys.argv[1])
files_dir = backup_dir / "files"
file_count = 0
for _, _, files in os.walk(files_dir):
    file_count += len(files)

manifest = {
    "domain": "storage-a",
    "generated_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    "backup_dir": str(backup_dir),
    "files": {"count": file_count},
}
(backup_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
PY

echo "STORAGE_A_BACKUP_OK=true"
echo "BACKUP_DIR=$BACKUP_DIR"
echo "MANIFEST=$BACKUP_DIR/manifest.json"
