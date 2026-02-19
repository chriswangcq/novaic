#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="${TMPDIR:-/tmp}/novaic-storage-ab-validate-$$"
DATA_DIR="$TMP_ROOT/data"
BACKUP_ROOT="$TMP_ROOT/backups"
REPORT_PATH="$ROOT_DIR/../ops-rounds/round-002/20-reports/team-storage-ab-validation-latest.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report-path)
      REPORT_PATH="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [--report-path PATH]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$DATA_DIR/files/images/agent-demo"
mkdir -p "$BACKUP_ROOT"

SAMPLE_FILE="$DATA_DIR/files/images/agent-demo/sample.txt"
echo "storage-ab-validation-payload" > "$SAMPLE_FILE"

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
        VALUES ('trs_demo_001', 'agent-demo', 'demo_tool', 'call-001', '{"text":"ok","files_created":[],"display_files":[]}', '2026-02-19T00:00:00Z')
        """
    )
PY

BACKUP_OUTPUT="$(bash "$ROOT_DIR/scripts/storage_ab_backup.sh" --data-dir "$DATA_DIR" --backup-root "$BACKUP_ROOT" --label "validation-run")"
BACKUP_DIR="$(printf "%s\n" "$BACKUP_OUTPUT" | awk -F= '/^BACKUP_DIR=/{print $2}')"

rm -f "$SAMPLE_FILE"
python - "$DATA_DIR/tool_results.db" <<'PY'
import sqlite3
import sys

db = sys.argv[1]
with sqlite3.connect(db) as conn:
    conn.execute("DELETE FROM tool_results")
PY

RESTORE_OUTPUT="$(bash "$ROOT_DIR/scripts/storage_ab_restore.sh" --backup-dir "$BACKUP_DIR" --target-dir "$DATA_DIR" --yes)"

python - "$DATA_DIR" <<'PY'
import sqlite3
import sys
from pathlib import Path

data_dir = Path(sys.argv[1])
sample = data_dir / "files" / "images" / "agent-demo" / "sample.txt"
if not sample.exists():
    raise SystemExit("validation failed: sample file not restored")

db = data_dir / "tool_results.db"
with sqlite3.connect(str(db)) as conn:
    row = conn.execute("SELECT COUNT(1) FROM tool_results WHERE result_id='trs_demo_001'").fetchone()
if not row or int(row[0]) != 1:
    raise SystemExit("validation failed: tool result row not restored")
PY

mkdir -p "$(dirname "$REPORT_PATH")"
{
  echo "# Storage-A/B Restore Validation Evidence"
  echo
  echo "- status: DONE"
  echo "- executed_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- command: \`bash novaic-backend/scripts/storage_ab_validate_restore.sh\`"
  echo "- temp_data_dir: \`$DATA_DIR\`"
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
  echo "## Validation Summary"
  echo "- file restore check: PASS (\`files/images/agent-demo/sample.txt\` restored)"
  echo "- db restore check: PASS (\`tool_results\` contains \`trs_demo_001\`)"
} > "$REPORT_PATH"

echo "VALIDATION_OK=true"
echo "EVIDENCE_REPORT=$REPORT_PATH"
