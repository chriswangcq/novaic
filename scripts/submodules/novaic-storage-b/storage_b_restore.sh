#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/.novaic}"
BACKUP_ROOT="${DATA_DIR}/backups/storage-b"
BACKUP_DIR=""
TARGET_DIR="$DATA_DIR"
YES="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup-dir)
      BACKUP_DIR="$2"
      shift 2
      ;;
    --backup-root)
      BACKUP_ROOT="$2"
      shift 2
      ;;
    --target-dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    --yes)
      YES="true"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--backup-dir DIR] [--backup-root DIR] [--target-dir DIR] [--yes]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$BACKUP_DIR" ]]; then
  if [[ ! -d "$BACKUP_ROOT" ]]; then
    echo "Backup root not found: $BACKUP_ROOT" >&2
    exit 1
  fi
  BACKUP_DIR="$(ls -1dt "$BACKUP_ROOT"/* 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
  echo "Backup dir not found. Use --backup-dir." >&2
  exit 1
fi

if [[ "$YES" != "true" && -f "$TARGET_DIR/tool_results.db" ]]; then
  echo "Target already has DB. Re-run with --yes to overwrite." >&2
  exit 1
fi

if [[ -f "$BACKUP_DIR/db/tool_results.db" ]]; then
  rm -f "$TARGET_DIR/tool_results.db" "$TARGET_DIR/tool_results.db-wal" "$TARGET_DIR/tool_results.db-shm"
  cp "$BACKUP_DIR/db/tool_results.db" "$TARGET_DIR/tool_results.db"
fi
if [[ -f "$BACKUP_DIR/db/tool_results.db-wal" ]]; then
  cp "$BACKUP_DIR/db/tool_results.db-wal" "$TARGET_DIR/tool_results.db-wal"
fi
if [[ -f "$BACKUP_DIR/db/tool_results.db-shm" ]]; then
  cp "$BACKUP_DIR/db/tool_results.db-shm" "$TARGET_DIR/tool_results.db-shm"
fi

echo "STORAGE_B_RESTORE_OK=true"
echo "RESTORED_FROM=$BACKUP_DIR"
echo "TARGET_DIR=$TARGET_DIR"
