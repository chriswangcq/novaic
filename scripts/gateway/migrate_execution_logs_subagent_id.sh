#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# migrate_execution_logs_subagent_id.sh
#
# One-time migration: rename legacy subagent_id = 'main' to
# 'main-{agent_id[:8]}' in execution_logs, matching the format used by
# new agent runs. After this migration the frontend compatibility shim
# (groupLogsBySubagent ignores bare 'main') can be removed.
#
# Usage (gateway can be running; SQLite WAL mode handles concurrent access):
#   bash scripts/migrate_execution_logs_subagent_id.sh [DB_PATH]
#
# Default DB_PATH: /opt/novaic/data/gateway.db
# ---------------------------------------------------------------------------
set -euo pipefail

DB_PATH="${1:-/opt/novaic/data/gateway.db}"

if [[ ! -f "$DB_PATH" ]]; then
  echo "ERROR: DB not found at $DB_PATH"
  exit 1
fi

echo "=== Backing up DB ==="
cp "$DB_PATH" "${DB_PATH}.backup_before_main_migration_$(date +%Y%m%d_%H%M%S)"

echo "=== Counting affected rows ==="
COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM execution_logs WHERE subagent_id = 'main';")
echo "Rows with subagent_id = 'main': $COUNT"

if [[ "$COUNT" -eq 0 ]]; then
  echo "Nothing to migrate. Exiting."
  exit 0
fi

echo "=== Running migration ==="
sqlite3 "$DB_PATH" <<'SQL'
BEGIN TRANSACTION;

UPDATE execution_logs
SET subagent_id = 'main-' || substr(agent_id, 1, 8)
WHERE subagent_id = 'main';

COMMIT;
SQL

echo "=== Verifying ==="
REMAINING=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM execution_logs WHERE subagent_id = 'main';")
echo "Remaining rows with subagent_id = 'main': $REMAINING"
echo "Migration complete."
