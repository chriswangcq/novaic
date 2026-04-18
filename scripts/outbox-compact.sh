#!/usr/bin/env bash
set -eo pipefail

DB_PATH="${ENTANGLED_DB_PATH:-$HOME/.novaic/data/entangled.db}"
RETENTION_DAYS=${1:-7}

echo "[outbox-compact] Deleting delivered messages older than $RETENTION_DAYS days from $DB_PATH..."

RETENTION_MS=$(( ( $(date +%s) - $RETENTION_DAYS * 86400 ) * 1000 ))

sqlite3 "$DB_PATH" <<EOF
DELETE FROM message_outbox 
WHERE delivered_at IS NOT NULL 
  AND delivered_at < $RETENTION_MS;
VACUUM;
EOF

echo "[outbox-compact] Done."
