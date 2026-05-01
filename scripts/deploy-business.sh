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
#     1. rsync 6 submodules to /opt/novaic/services/
#        (novaic-business + Entangled + novaic-common +
#         novaic-gateway + novaic-device + novaic-agent-runtime)
#        ** All 4 "caller" services MUST go together with novaic-common **
#        because PR-05 made service_name a required positional arg of
#        internal_{sync,async}_client. A partial deploy crashes hw_status
#        etc. with TypeError: missing 1 required positional argument:
#        'service_name'. (TD-2, 2026-04-20: ``internal_client`` alias
#        removed; the underlying requirement is unchanged.)
#     2. rsync scripts/start.sh → /opt/novaic/start.sh (prod's actual path)
#     3. rsync scripts/canary/ → /opt/novaic/services/scripts/canary/
#     4. Graceful stop + start
#
#   --first-time mode (additionally):
#     1. Backup entangled.db + /opt/novaic/start.sh with timestamp suffix
#     2. Take a full snapshot tarball of /opt/novaic/services/ (rollback target)
#     3. rsync with verbose diff listing
#     4. Start services; subscriber is required and starts with the stack.
#     5. Wait 60s for Entangled ensure_schema to create message_outbox table
#     6. Health-check all backend services (curl /health)
#     7. Verify message_outbox schema exists
#     8. Print rollback instructions
#
# Post-deploy (operator-driven, NOT automated by this script):
#   TD-5 (2026-04-15) flow — edit the OVERLAY file, never services.json.
#   The overlay lives outside $REMOTE_ROOT so rsync cannot stomp it.
#     1. Edit /opt/novaic/etc/runtime_switches.json (single file, all
#        services read it via common/strict_config.py overlay merge):
#          {
#            "health_check_interval_seconds": 5,
#            "scheduler_poll_interval_seconds": 1.0
#          }
#        Only keys already defined in services.json's runtime_switches
#        section are allowed — typos crash loudly at startup.
#     2. bash /opt/novaic/start.sh --stop
#        bash /opt/novaic/start.sh
#     3. Verify the runtime cadence snapshot in service logs.
#   Editing services.json on prod is a dead end — the overlay wins at
#   load time and the next rsync stomps your edit anyway.
#
# Safety:
#   - --first-time ALWAYS backs up DB before touching code.
#   - Snapshot tarball lives at /opt/novaic/snapshots/ for rollback.
#   - Subscriber is a required part of the backend stack, not a canary flag.

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
# novaic-cortex ships with the runtime stack; subscriber may read Cortex
# scope meta for stale-claim probes, but does not write scope inputs.
for d in novaic-business Entangled novaic-common novaic-cortex novaic-gateway novaic-device novaic-agent-runtime scripts; do
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
    # TD-5 (2026-04-15): runtime_switches.json lives on prod as an
    # overlay (canonical path: /opt/novaic/etc/runtime_switches.json,
    # read by common/strict_config.py). Excluding the per-service
    # sibling form belt-and-braces: if anyone ever drops a sibling
    # on prod we never stomp it during rsync.
    --exclude 'runtime_switches.json'
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
    # -L (--copy-links) is required because several submodules have
    # `common` as a symlink -> ../novaic-common/common for local dev;
    # prod has them as real directory copies. Without -L, rsync fails
    # with "cannot delete non-empty directory" when trying to replace
    # a populated dir with a symlink.
    rsync -azL --delete "${RSYNC_EXCLUDES[@]}" \
        "$src_path/" "$TARGET:$dst_path/"
}

rsync_one novaic-business
rsync_one Entangled
rsync_one novaic-common
# PR-05 contract is transitive: novaic-common signature change forces all
# callers to ship together. Any partial deploy produces TypeError at runtime.
rsync_one novaic-gateway
rsync_one novaic-device
rsync_one novaic-agent-runtime
# Cortex hosts the scope lifecycle APIs used by runtime workers and
# subscriber stale-claim probes; ship it with the backend stack.
rsync_one novaic-cortex

# scripts/start.sh deploys to prod's flat /opt/novaic/start.sh (NOT under services/)
echo "  [rsync] scripts/start.sh → $TARGET:$REMOTE_START_SCRIPT"
rsync -az --chmod=u+rx "$REPO_ROOT/scripts/start.sh" "$TARGET:$REMOTE_START_SCRIPT"

# scripts/canary/ is an operator tool; mirror to services/scripts/canary/
echo "  [rsync] scripts/canary/ → $TARGET:$REMOTE_ROOT/scripts/canary/"
ssh "$TARGET" "mkdir -p $REMOTE_ROOT/scripts/canary"
rsync -az --delete "${RSYNC_EXCLUDES[@]}" \
    "$REPO_ROOT/scripts/canary/" "$TARGET:$REMOTE_ROOT/scripts/canary/"

echo ""

# ── Seed runtime_switches overlay (TD-5) ─────────────────────────────────────
# The committed services.json carries defaults. common/strict_config.py
# deep-merges an optional overlay at /opt/novaic/etc/runtime_switches.json.
# That file lives outside $REMOTE_ROOT so rsync cannot touch it. The block
# below seeds the overlay on the first deploy only.
echo "=== Seeding runtime_switches overlay (TD-5, idempotent) ==="
REMOTE_OVERLAY="/opt/novaic/etc/runtime_switches.json"
ssh "$TARGET" bash -s <<EOF
set -eu
mkdir -p /opt/novaic/etc
if [ -f "$REMOTE_OVERLAY" ]; then
    echo "  overlay already exists → preserved as operator-owned source of truth"
    echo "  current contents:"
    cat "$REMOTE_OVERLAY" | sed 's/^/    /'
else
    # Seed with committed defaults from the freshly-rsynced
    # novaic-common/config/services.json.
    python3 - <<'PYEOF'
import json
import pathlib

src = pathlib.Path("/opt/novaic/services/novaic-common/config/services.json")
dst = pathlib.Path("/opt/novaic/etc/runtime_switches.json")
payload = json.loads(src.read_text())
dst.write_text(json.dumps(payload["runtime_switches"], indent=2, sort_keys=True) + "\n")
print(f"  seeded {dst} from {src}")
print(f"  initial contents: {dst.read_text().rstrip()}")
PYEOF
fi
EOF
echo ""

# ── Start services ───────────────────────────────────────────────────────────
# Runtime cadence changes are one-file edits to /opt/novaic/etc/runtime_switches.json
# plus restart. services.json copies in $REMOTE_ROOT are rsync-owned.
echo "=== Starting services ==="
ssh "$TARGET" "bash $REMOTE_START_SCRIPT"
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

    echo "[7/8] Checking for Traceback / ERROR across all service logs..."
    SVC_ERR_REPORT=$(ssh "$TARGET" bash -s <<'REMOTE'
set -eu
TODAY=$(date +%Y%m%d)
for name in business device gateway entangled queue-service cortex health; do
    # Prefer date-suffixed log, fall back to flat .log
    f="/opt/novaic/data/logs/${name}-${TODAY}.log"
    [ -f "$f" ] || f="/opt/novaic/data/logs/${name}.log"
    [ -f "$f" ] || continue
    n=$(grep -cE 'ERROR|Traceback' "$f" 2>/dev/null || true)
    # grep -c prints one line per file even when 0, keep first integer
    n=$(echo "$n" | head -1 | tr -dc '0-9')
    [ -z "$n" ] && n=0
    echo "  $name ($f): $n ERROR/Traceback lines"
    if [ "$n" -gt 0 ]; then
        echo "    --- first 5 ---"
        grep -E 'Traceback|ERROR' "$f" | head -5 | sed 's/^/    /'
    fi
done
REMOTE
    )
    echo "$SVC_ERR_REPORT"
    echo ""

    echo "[8/8] Confirming subscriber process was started..."
    ssh "$TARGET" "pgrep -af main_subscriber.py || true"
    echo ""

    echo "================================================================="
    echo "  First-time deploy COMPLETE."
    echo "================================================================="
    cat <<NEXT

  Next steps (operator-driven, manual):

  1. Let the system run for 30 min to verify cold-start stability.
     Watch for:
       ssh $TARGET "tail -F $REMOTE_DATA/logs/business-\$(date +%Y%m%d).log | grep -E 'ERROR|Traceback|agent_owner_lookup.*miss|caller=unknown'"
     All should remain empty.

  2. Runtime cadence changes use the overlay flow:
       edit /opt/novaic/etc/runtime_switches.json:
         {
           "health_check_interval_seconds": 5,
           "scheduler_poll_interval_seconds": 1.0
         }
       then:
         ssh $TARGET "bash $REMOTE_START_SCRIPT --stop && bash $REMOTE_START_SCRIPT"
       (The overlay survives rsync; editing services.json has no effect.)

  3. Normal restart:
       ssh $TARGET "bash $REMOTE_START_SCRIPT --stop && bash $REMOTE_START_SCRIPT"

  4. Full code rollback:
       ssh $TARGET "cd /opt/novaic && tar xzf snapshots/services-$TIMESTAMP.tar.gz"
       ssh $TARGET "cp $REMOTE_SNAPSHOT_DIR/entangled.db.bak-$TIMESTAMP $REMOTE_DATA/entangled.db"
       ssh $TARGET "cp $REMOTE_SNAPSHOT_DIR/start.sh.bak-$TIMESTAMP $REMOTE_START_SCRIPT"
       ssh $TARGET "bash $REMOTE_START_SCRIPT"

NEXT
else
    echo "================================================================="
    echo "  Incremental deploy COMPLETE."
    echo "================================================================="
    echo ""
    echo "  Verify: ssh $TARGET 'curl -s localhost:19998/health'"
    echo ""
fi
