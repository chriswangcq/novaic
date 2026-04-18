#!/usr/bin/env bash
# NovAIC Business/Subscriber Stack — Production Deploy Script (PR-17)
#
# Purpose:
#   Deploy novaic-business + Entangled + novaic-common + scripts/start.sh
#   to production, covering the "Phase 1 + Phase 2 first-time upload" case
#   (生产代码 pre-PR-15 的首次集成上线) as well as incremental updates.
#
# Usage:
#   scripts/deploy-business.sh user@host                  # incremental
#   scripts/deploy-business.sh user@host --first-time     # full cold deploy
#
# Production layout (verified 2026-04-18 on api.gradievo.com):
#   /opt/novaic/start.sh                 # the actual start script (flat path, NOT under services/)
#   /opt/novaic/services/novaic-*        # per-service code trees
#   /opt/novaic/services/novaic-business/business/subscribers/   # NEW (PR-15+)
#   /opt/novaic/services/scripts/canary/ # NEW (PR-17, operator tools)
#   /opt/novaic/data/entangled.db        # SQLite with message_outbox (PR-14+)
#   /opt/novaic/data/logs/               # Rotated logs
#   /opt/novaic/snapshots/               # Created by this script
#
# What it does:
#   Incremental mode (default):
#     1. rsync 3 submodules to /opt/novaic/services/
#     2. rsync scripts/start.sh → /opt/novaic/start.sh (prod's actual path)
#     3. rsync scripts/canary/ → /opt/novaic/services/scripts/canary/
#     4. Graceful stop + start (subscriber flag preserved from env)
#
#   --first-time mode (additionally):
#     1. Backup entangled.db + /opt/novaic/start.sh with timestamp suffix
#     2. Take a full snapshot tarball of /opt/novaic/services/ (rollback target)
#     3. rsync with verbose diff listing
#     4. Start with SUBSCRIBER FLAG OFF (冷启动验证，不急开 subscriber)
#     5. Wait 60s for Entangled ensure_schema to create message_outbox table
#     6. Health-check all backend services (curl /health)
#     7. Verify message_outbox schema exists
#     8. Print next-step instructions (do NOT auto-enable subscriber)
#
# Post-deploy (operator-driven, NOT automated by this script):
#   To enter Canary 阶段 1, on the production host:
#     export NOVAIC_ENABLE_SUBSCRIBER=1
#     export NOVAIC_HEALTH_CHECK_INTERVAL=5
#     bash /opt/novaic/start.sh --stop
#     bash /opt/novaic/start.sh
#
# Safety:
#   - --first-time ALWAYS backs up DB before touching code.
#   - Snapshot tarball lives at /opt/novaic/snapshots/ for rollback.
#   - This script never auto-enables the subscriber flag.

set -euo pipefail

# ── Args ─────────────────────────────────────────────────────────────────────
if [ $# -lt 1 ]; then
    cat <<EOF
Usage: $0 user@host [--first-time]
  user@host     SSH target (e.g. root@api.gradievo.com)
  --first-time  Full cold deploy with DB backup, snapshot, and health checks.
                Required for the first PR-14/15/16 rollout to production.
EOF
    exit 1
fi

TARGET="$1"
MODE="incremental"
if [ "${2:-}" = "--first-time" ]; then
    MODE="first-time"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

REMOTE_ROOT="/opt/novaic/services"
REMOTE_DATA="/opt/novaic/data"
REMOTE_SNAPSHOT_DIR="/opt/novaic/snapshots"
REMOTE_START_SCRIPT="/opt/novaic/start.sh"

echo "================================================================="
echo "  NovAIC Business Deploy (PR-17)"
echo "================================================================="
echo "  Target:  $TARGET"
echo "  Mode:    $MODE"
echo "  Source:  $REPO_ROOT"
echo "  Time:    $TIMESTAMP"
echo "================================================================="
echo ""

# ── Sanity: source dirs exist ────────────────────────────────────────────────
for d in novaic-business Entangled novaic-common scripts; do
    if [ ! -d "$REPO_ROOT/$d" ]; then
        echo "ERROR: $REPO_ROOT/$d does not exist" >&2
        exit 1
    fi
done

# ── RSYNC excludes (shared) ──────────────────────────────────────────────────
RSYNC_EXCLUDES=(
    --exclude '.git'
    --exclude '.github'
    --exclude '__pycache__'
    --exclude '*.pyc'
    --exclude '.venv'
    --exclude 'venv'
    --exclude '.env'
    --exclude '.pytest_cache'
    --exclude '.mypy_cache'
    --exclude '.ruff_cache'
    --exclude 'node_modules'
    --exclude '*.log'
    --exclude 'logs/'
    --exclude '*.db'
    --exclude '*.db-journal'
    --exclude '*.db-wal'
    --exclude '*.db-shm'
    --exclude '.DS_Store'
)

# ── first-time only: DB backup + code snapshot ───────────────────────────────
if [ "$MODE" = "first-time" ]; then
    echo "=== [first-time] Pre-flight safety net ==="
    echo ""
    echo "[1/8] Stopping all services on $TARGET (so rsync doesn't race)..."
    ssh "$TARGET" "bash $REMOTE_START_SCRIPT --stop" || true
    echo ""

    echo "[2/8] Backing up entangled.db + current start.sh..."
    ssh "$TARGET" bash -s <<EOF
set -eu
mkdir -p $REMOTE_SNAPSHOT_DIR
if [ -f $REMOTE_DATA/entangled.db ]; then
    cp -p $REMOTE_DATA/entangled.db $REMOTE_SNAPSHOT_DIR/entangled.db.bak-$TIMESTAMP
    echo "  entangled.db backed up to $REMOTE_SNAPSHOT_DIR/entangled.db.bak-$TIMESTAMP"
    ls -lh $REMOTE_SNAPSHOT_DIR/entangled.db.bak-$TIMESTAMP
else
    echo "  WARN: $REMOTE_DATA/entangled.db does not exist; nothing to backup"
fi
if [ -f $REMOTE_START_SCRIPT ]; then
    cp -p $REMOTE_START_SCRIPT $REMOTE_SNAPSHOT_DIR/start.sh.bak-$TIMESTAMP
    echo "  start.sh backed up to $REMOTE_SNAPSHOT_DIR/start.sh.bak-$TIMESTAMP"
fi
EOF
    echo ""

    echo "[3/8] Snapshotting current /opt/novaic/services (code rollback target)..."
    ssh "$TARGET" bash -s <<EOF
set -eu
mkdir -p $REMOTE_SNAPSHOT_DIR
if [ -d $REMOTE_ROOT ]; then
    tar czf $REMOTE_SNAPSHOT_DIR/services-$TIMESTAMP.tar.gz \
        --exclude='*.venv*' --exclude='__pycache__' --exclude='*.pyc' \
        -C $(dirname $REMOTE_ROOT) $(basename $REMOTE_ROOT) 2>/dev/null || true
    echo "  snapshot saved: $REMOTE_SNAPSHOT_DIR/services-$TIMESTAMP.tar.gz"
    ls -lh $REMOTE_SNAPSHOT_DIR/services-$TIMESTAMP.tar.gz
else
    echo "  WARN: $REMOTE_ROOT does not exist yet (new host?); skipping snapshot"
fi
EOF
    echo ""
fi

# ── Rsync: 3 submodules + scripts/ ───────────────────────────────────────────
echo "=== Rsyncing code to $TARGET:$REMOTE_ROOT ==="
echo ""

rsync_one() {
    local src_name="$1"
    local src_path="$REPO_ROOT/$src_name"
    local dst_path="$REMOTE_ROOT/$src_name"
    echo "  [rsync] $src_name/ → $TARGET:$dst_path/"
    ssh "$TARGET" "mkdir -p $dst_path"
    rsync -az --delete "${RSYNC_EXCLUDES[@]}" \
        "$src_path/" "$TARGET:$dst_path/"
}

rsync_one novaic-business
rsync_one Entangled
rsync_one novaic-common

# scripts/start.sh deploys to prod's flat /opt/novaic/start.sh (NOT under services/)
echo "  [rsync] scripts/start.sh → $TARGET:$REMOTE_START_SCRIPT"
rsync -az --chmod=u+rx "$REPO_ROOT/scripts/start.sh" "$TARGET:$REMOTE_START_SCRIPT"

# scripts/canary/ is an operator tool; mirror to services/scripts/canary/
echo "  [rsync] scripts/canary/ → $TARGET:$REMOTE_ROOT/scripts/canary/"
ssh "$TARGET" "mkdir -p $REMOTE_ROOT/scripts/canary"
rsync -az --delete "${RSYNC_EXCLUDES[@]}" \
    "$REPO_ROOT/scripts/canary/" "$TARGET:$REMOTE_ROOT/scripts/canary/"

echo ""

# ── Start services (subscriber flag OFF always — operator must opt-in) ───────
echo "=== Starting services (subscriber flag OFF for cold start) ==="
ssh "$TARGET" bash -s <<EOF
# Explicitly unset canary flags; this deploy NEVER auto-enables subscriber.
unset NOVAIC_ENABLE_SUBSCRIBER || true
unset NOVAIC_HEALTH_CHECK_INTERVAL || true
bash $REMOTE_START_SCRIPT
EOF
echo ""

# ── first-time only: verify schema + health ──────────────────────────────────
if [ "$MODE" = "first-time" ]; then
    echo "=== [first-time] Post-start verification ==="
    echo ""
    echo "[4/8] Waiting 60s for Entangled ensure_schema to run (message_outbox creation)..."
    sleep 60
    echo ""

    echo "[5/8] Verifying message_outbox schema exists..."
    SCHEMA_OUT=$(ssh "$TARGET" "sqlite3 $REMOTE_DATA/entangled.db '.schema message_outbox'")
    if [ -z "$SCHEMA_OUT" ]; then
        echo "  FAIL: message_outbox table not created in entangled.db"
        echo "  Check Entangled startup logs: ssh $TARGET 'tail -50 $REMOTE_DATA/logs/entangled.log'"
        exit 1
    fi
    echo "  OK: message_outbox schema present"
    echo "$SCHEMA_OUT" | sed 's/^/    /'
    echo ""

    echo "[6/8] Health check: all backend services..."
    for port_name in "19900:entangled" "19999:gateway" "19998:business" "19993:device" "19997:queue" "19995:file" "19996:cortex"; do
        port="${port_name%%:*}"
        name="${port_name##*:}"
        if ssh "$TARGET" "curl -sSf -m 3 http://127.0.0.1:$port/health >/dev/null 2>&1 || curl -sSf -m 3 http://127.0.0.1:$port/api/health >/dev/null 2>&1"; then
            echo "  OK: $name :$port"
        else
            echo "  WARN: $name :$port not healthy (may still be warming up)"
        fi
    done
    echo ""

    echo "[7/8] Checking for Traceback / ERROR in business startup log..."
    ERR_COUNT=$(ssh "$TARGET" "grep -cE 'Traceback|ERROR' $REMOTE_DATA/logs/business-\$(date +%Y%m%d).log 2>/dev/null || echo 0")
    if [ "$ERR_COUNT" -gt 0 ]; then
        echo "  WARN: $ERR_COUNT ERROR/Traceback lines in business log; inspect before Canary:"
        ssh "$TARGET" "grep -E 'Traceback|ERROR' $REMOTE_DATA/logs/business-\$(date +%Y%m%d).log | head -20"
    else
        echo "  OK: no Traceback/ERROR in business log"
    fi
    echo ""

    echo "[8/8] Confirming subscriber is OFF (cold start correctness)..."
    ssh "$TARGET" "grep 'dispatch_subscriber' $REMOTE_DATA/logs/business-\$(date +%Y%m%d).log | tail -3" || true
    echo ""

    echo "================================================================="
    echo "  First-time deploy COMPLETE."
    echo "================================================================="
    cat <<NEXT

  Next steps (operator-driven, manual):

  1. Let the system run flag-OFF for 30 min to verify cold-start stability.
     Watch for:
       ssh $TARGET "tail -F $REMOTE_DATA/logs/business-\$(date +%Y%m%d).log | grep -E 'ERROR|Traceback|agent_owner_lookup.*miss|caller=unknown'"
     All should remain empty.

  2. If clean, enter Canary 阶段 1 (subscriber ON, 4-6h observation):
       ssh $TARGET bash -c '"
         export NOVAIC_ENABLE_SUBSCRIBER=1
         export NOVAIC_HEALTH_CHECK_INTERVAL=5
         bash $REMOTE_START_SCRIPT --stop
         bash $REMOTE_START_SCRIPT
       "'

  3. Rollback (if anything goes wrong):
       ssh $TARGET bash -c '"
         unset NOVAIC_ENABLE_SUBSCRIBER
         unset NOVAIC_HEALTH_CHECK_INTERVAL
         bash $REMOTE_START_SCRIPT --stop
         bash $REMOTE_START_SCRIPT
       "'

  4. Full code rollback (if subscriber rollback insufficient):
       ssh $TARGET "cd /opt/novaic && tar xzf snapshots/services-$TIMESTAMP.tar.gz"
       ssh $TARGET "cp $REMOTE_SNAPSHOT_DIR/entangled.db.bak-$TIMESTAMP $REMOTE_DATA/entangled.db"
       ssh $TARGET "cp $REMOTE_SNAPSHOT_DIR/start.sh.bak-$TIMESTAMP $REMOTE_START_SCRIPT"
       ssh $TARGET "bash $REMOTE_START_SCRIPT"

  Reference: docs/runbooks/subscriber-canary.md

NEXT
else
    echo "================================================================="
    echo "  Incremental deploy COMPLETE."
    echo "================================================================="
    echo ""
    echo "  Verify: ssh $TARGET 'curl -s localhost:19998/health'"
    echo ""
fi
