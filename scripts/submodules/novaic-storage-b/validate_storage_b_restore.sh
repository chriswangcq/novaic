#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-storage-b-validate-$$"
DATA_DIR="$TMP_ROOT/data"
BACKUP_ROOT="$TMP_ROOT/backups"
RESTORE_TARGET="$TMP_ROOT/restore-target"
REPORT_PATH="$ROOT_DIR/artifacts/storage-b-restore-validate-latest.md"

mkdir -p "$DATA_DIR" "$BACKUP_ROOT" "$RESTORE_TARGET" "$(dirname "$REPORT_PATH")"

python - "$DATA_DIR/tool_results.db" <<'PY'
import sqlite3
import sys

db = sys.argv[1]
with sqlite3.connect(db) as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tool_results (
            result_id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            tool_call_id TEXT,
            normalized TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO tool_results (result_id, agent_id, tool_name, tool_call_id, normalized, created_at)
        VALUES ('trs_b_demo_001', 'agent-b', 'demo', 'call-b-001', '{"text":"ok","files_created":[],"display_files":[]}', '2026-02-20T00:00:00Z')
        """
    )
PY

BACKUP_OUTPUT="$(bash "$ROOT_DIR/scripts/storage_b_backup.sh" --data-dir "$DATA_DIR" --backup-root "$BACKUP_ROOT" --label "validation-run")"
BACKUP_DIR="$(printf "%s\n" "$BACKUP_OUTPUT" | awk -F= '/^BACKUP_DIR=/{print $2}')"

python - "$DATA_DIR/tool_results.db" <<'PY'
import sqlite3
import sys
with sqlite3.connect(sys.argv[1]) as conn:
    conn.execute("DELETE FROM tool_results")
PY

RESTORE_OUTPUT="$(bash "$ROOT_DIR/scripts/storage_b_restore.sh" --backup-dir "$BACKUP_DIR" --target-dir "$RESTORE_TARGET" --yes)"

python - "$RESTORE_TARGET/tool_results.db" <<'PY'
import sqlite3
import sys

with sqlite3.connect(sys.argv[1]) as conn:
    row = conn.execute("SELECT COUNT(1) FROM tool_results WHERE result_id='trs_b_demo_001'").fetchone()
if not row or int(row[0]) != 1:
    raise SystemExit("STORAGE_B_RESTORE_VALIDATE=FAIL")
print("STORAGE_B_RESTORE_VALIDATE=PASS")
PY

{
  echo "# Storage-B Restore Validation Evidence"
  echo
  echo "- command: \`bash scripts/validate_storage_b_restore.sh\`"
  echo "- expected_marker: \`STORAGE_B_RESTORE_VALIDATE=PASS\`"
  echo "- backup_dir: \`$BACKUP_DIR\`"
  echo
  echo "## Backup Output"
  echo '```'
  printf "%s\n" "$BACKUP_OUTPUT"
  echo '```'
  echo
  echo "## Restore Output"
  echo '```'
  printf "%s\n" "$RESTORE_OUTPUT"
  echo '```'
  echo
  echo "- STORAGE_B_RESTORE_VALIDATE=PASS"
} > "$REPORT_PATH"

echo "STORAGE_B_RESTORE_VALIDATE=PASS"
echo "STORAGE_B_RESTORE_REPORT=$REPORT_PATH"
