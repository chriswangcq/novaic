#!/usr/bin/env bash
# NovAIC Backend Start Script (Linux/Cloud)
#
# Configuration:
#   services.json = defaults + secrets (jwt_secret)
#   CLI args      = production overrides (visible in ps aux)
#   Zero exports  — all config passed as CLI args or read from services.json.
#
# Services:
#   - Entangled      :19900  Entity CRUD (single source of truth) + WS Sync
#   - Gateway        :19999  Auth, App WS signaling, log broadcast, file proxy
#   - Business       :19998  All /internal/* APIs, Entangled action hooks, schema push
#   - Device         :19993  PC bridge WS, VM lifecycle, SSH key mgmt, WebRTC signaling
#   - Queue Service  :19997  Task/Saga queue management
#   - File Service   :19995  File upload/download
#   - Cortex         :19996  LLM orchestration, Workspace, Recall, Sandbox
#   - Workers        task-worker ×4, saga-worker ×2, health ×1, scheduler ×1
#
# Communication:
#   Workers → Business  (direct /internal/* calls)
#   Workers → Gateway   (only /api/logs/broadcast for WS push)
#   Workers → Entangled (direct entity CRUD)
#   Entangled → Business (action hook callbacks)
#   Business → Device   (device action hook proxy)
#   Device → Gateway    (WebRTC signaling via /api/app/push)

set -euo pipefail

BASE="/opt/novaic/services"
DATA_DIR="/opt/novaic/data"
LOG_DIR="$DATA_DIR/logs"
HOST="127.0.0.1"
mkdir -p "$LOG_DIR"

# ── Ports ────────────────────────────────────────────────────────────────────

PORT_ENTANGLED=19900
PORT_GATEWAY=19999
PORT_BUSINESS=19998
PORT_QUEUE_SERVICE=19997
PORT_CORTEX=19996
PORT_FILE_SERVICE=19995
PORT_DEVICE=19993

# ── Canary / Subscriber / Health cadence (PR-33 Phase 3, 2026-04-20) ─────────
# Historical (pre-PR-33): NOVAIC_ENABLE_SUBSCRIBER / NOVAIC_HEALTH_CHECK_INTERVAL
# env bridges injected --enable-subscriber and --check-interval here. Both are
# deleted — the three values they controlled now live under
# services.json → runtime_switches.{subscriber_enabled,
# health_check_interval_seconds, scheduler_poll_interval_seconds}. See
# docs/roadmap/tickets/PR-33-env-shrink.md §C.2 and
# docs/runbooks/subscriber-canary.md for the flip procedure (edit + restart).
# The log_startup_snapshot() INFO line in each service/worker is now the only
# audit trail for which switches this process believes in.

# ── Derived URLs (used only as CLI arg values below) ─────────────────────────

ENTANGLED_URL="http://$HOST:$PORT_ENTANGLED"
GW_URL="http://$HOST:$PORT_GATEWAY"
BIZ_URL="http://$HOST:$PORT_BUSINESS"
QS_URL="http://$HOST:$PORT_QUEUE_SERVICE"
FS_URL="http://$HOST:$PORT_FILE_SERVICE"
DEV_URL="http://$HOST:$PORT_DEVICE"
CORTEX_URL="http://$HOST:$PORT_CORTEX"

py() { echo "$BASE/$1/.venv/bin/python"; }

port_in_use() { lsof -ti :"$1" >/dev/null 2>&1; }

wait_port() {
    local port="$1" name="$2" secs="${3:-20}"
    for i in $(seq 1 $((secs * 4))); do
        if port_in_use "$port"; then echo "  OK: $name :$port"; return 0; fi
        sleep 0.25
    done
    echo "  WARN: $name did not bind :$port within ${secs}s"
}

wait_port_free() {
    local port="$1" secs="${2:-10}"
    for i in $(seq 1 $((secs * 4))); do
        if ! port_in_use "$port"; then return 0; fi
        sleep 0.25
    done
    echo "  WARN: port $port still in use after ${secs}s"
}

stop() {
    # PR-34 34d: subscriber is an independent subprocess. Give it SIGTERM
    # first so the in-flight claim finishes cleanly (avoids leaving a row
    # half-claimed, which would block for claim_ttl_ms=30s under the next
    # subscriber). A short grace window then SIGKILL as usual.
    pkill -TERM -f "main_subscriber.py" 2>/dev/null || true
    # 15 × 0.2s = 3s graceful window. Matches claim_ttl_ms/10 ≈ 3s budget.
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
        pgrep -f "main_subscriber.py" >/dev/null 2>&1 || break
        sleep 0.2
    done
    pkill -9 -f "main_subscriber.py" 2>/dev/null || true

    pkill -9 -f "entangled.app.main" 2>/dev/null || true
    pkill -9 -f "main_gateway.py" 2>/dev/null || true
    pkill -9 -f "main_business.py" 2>/dev/null || true
    pkill -9 -f "main_device.py" 2>/dev/null || true
    pkill -9 -f "main_novaic.py" 2>/dev/null || true
    pkill -9 -f "main_file_service.py" 2>/dev/null || true
    pkill -9 -f "main_cortex" 2>/dev/null || true
    pkill -9 -f "main_runtime_orchestrator.py" 2>/dev/null || true
    sleep 2
    echo "Stopped."
}

[ "${1:-}" = "--stop" ] && stop && exit 0

stop 2>/dev/null || true

for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_FILE_SERVICE $PORT_CORTEX; do
    wait_port_free "$port" 8
done

echo "Starting NovAIC backends..."

# ── Secrets (read from services.json, pass as CLI args) ──────────────────────

_cfg() { python3 -c "import json; d=json.load(open('$BASE/novaic-common/config/services.json')); print(eval('d'+\"$1\"))"; }

JWT_SECRET=$(_cfg "['secrets']['jwt_secret']")
OSS_AK=$(_cfg "['secrets']['alibaba_cloud_access_key_id']")
OSS_SK=$(_cfg "['secrets']['alibaba_cloud_access_key_secret']")
OSS_ENDPOINT=$(_cfg "['cortex']['oss_endpoint']")
OSS_REGION=$(_cfg "['cortex']['oss_region']")
OSS_BUCKET=$(_cfg "['cortex']['oss_bucket']")
CORTEX_INTERNAL_KEY=$(_cfg "['secrets']['cortex_internal_key']")

# ── Services (all config passed as explicit CLI args — no exports) ───────────

PYTHONPATH="$BASE/Entangled/packages/server-python:${PYTHONPATH:-}" \
$(py novaic-gateway) -m entangled.app.main \
    --host "$HOST" --port "$PORT_ENTANGLED" \
    --db-path "$DATA_DIR/entangled.db" \
    --service-token "$JWT_SECRET" \
    >> "$LOG_DIR/entangled.log" 2>&1 &
wait_port "$PORT_ENTANGLED" "Entangled Service"

PYTHONPATH="$BASE/Entangled/packages/server-python:$BASE/novaic-common:$BASE/novaic-shared-kernel:$BASE/novaic-contracts:${PYTHONPATH:-}" \
$(py novaic-gateway) "$BASE/novaic-gateway/main_gateway.py" \
    --host "$HOST" --port "$PORT_GATEWAY" --data-dir "$DATA_DIR" \
    --queue-service-url "$QS_URL" --file-service-url "$FS_URL" \
    --entangled-url "$ENTANGLED_URL" \
    >> "$LOG_DIR/gateway-$(date +%Y%m%d).log" 2>&1 &
wait_port "$PORT_GATEWAY" "Gateway" 30

PYTHONPATH="$BASE/Entangled/packages/server-python:$BASE/novaic-common:$BASE/novaic-business:${PYTHONPATH:-}" \
$(py novaic-gateway) "$BASE/novaic-business/main_business.py" \
    --host "$HOST" --port "$PORT_BUSINESS" --data-dir "$DATA_DIR" \
    --entangled-url "$ENTANGLED_URL" --gateway-url "$GW_URL" \
    >> "$LOG_DIR/business-$(date +%Y%m%d).log" 2>&1 &
wait_port "$PORT_BUSINESS" "Business Service"
# PR-33 Phase 3: canary "NOTE" removed. Check runtime_switches in business.log:
#   grep "runtime_switches=" "$LOG_DIR/business-$(date +%Y%m%d).log" | head -1

PYTHONPATH="$BASE/Entangled/packages/server-python:$BASE/novaic-common:$BASE/novaic-device:${PYTHONPATH:-}" \
$(py novaic-gateway) "$BASE/novaic-device/main_device.py" \
    --host "$HOST" --port "$PORT_DEVICE" --data-dir "$DATA_DIR" \
    --gateway-url "$GW_URL" --business-url "$BIZ_URL" \
    >> "$LOG_DIR/device-$(date +%Y%m%d).log" 2>&1 &
wait_port "$PORT_DEVICE" "Device Service"

$(py novaic-agent-runtime) "$BASE/novaic-agent-runtime/main_novaic.py" queue-service \
    --host "$HOST" --port "$PORT_QUEUE_SERVICE" --data-dir "$DATA_DIR" \
    >> "$LOG_DIR/queue-service.log" 2>&1 &
wait_port "$PORT_QUEUE_SERVICE" "Queue Service"

$(py novaic-storage-a) "$BASE/novaic-storage-a/main_file_service.py" \
    --host "$HOST" --port "$PORT_FILE_SERVICE" --data-dir "$DATA_DIR" \
    >> "$LOG_DIR/file-service.log" 2>&1 &
wait_port "$PORT_FILE_SERVICE" "File Service"

mkdir -p "$DATA_DIR/cortex"
# P3-6: Redis-backed scope lock (MANDATORY). Loopback-only redis-server
# runs on the same host (systemd unit `redis-server.service`, bound to
# 127.0.0.1). Cortex refuses to start without a reachable Redis —
# per-root-scope serialization (INV-1, INV-7) is held by Redis
# `SET NX PX` + Lua release + heartbeat (see
# ``novaic_cortex/scope_locks.py::RedisScopeLockManager``). Multi-worker /
# multi-replica Cortex is therefore always safe.
# PR-06 (2026-04-15): cortex/api.py imports common.middlewares.caller_logging
# for the caller-logging middleware. Cortex runs out of its own venv
# (novaic-cortex/.venv) which doesn't ship novaic-common as a pkg;
# export PYTHONPATH so the import resolves to the sibling submodule.
CORTEX_STORE_ROOT="$DATA_DIR/cortex" \
PYTHONPATH="$BASE/novaic-common:${PYTHONPATH:-}" \
$(py novaic-cortex) -m novaic_cortex.main_cortex \
    --host "$HOST" --port "$PORT_CORTEX" \
    --jwt-secret "$JWT_SECRET" \
    --business-url "$BIZ_URL" --internal-key "$CORTEX_INTERNAL_KEY" \
    --oss-ak "$OSS_AK" --oss-sk "$OSS_SK" \
    --oss-endpoint "$OSS_ENDPOINT" --oss-region "$OSS_REGION" --oss-bucket "$OSS_BUCKET" \
    --redis-url "redis://127.0.0.1:6379/0" \
    --redis-lock-ttl-seconds 300 \
    >> "$LOG_DIR/cortex.log" 2>&1 &
wait_port "$PORT_CORTEX" "Cortex"

# ── Workers (every URL passed explicitly — visible in ps aux) ────────────────

PY=$(py novaic-agent-runtime)
MAIN="$BASE/novaic-agent-runtime/main_novaic.py"
WORKER_ARGS="--gateway-url $GW_URL --business-url $BIZ_URL --queue-service-url $QS_URL --cortex-url $CORTEX_URL --data-dir $DATA_DIR"

for pool in control execution; do
    for i in 1 2; do
        $PY $MAIN task-worker $WORKER_ARGS \
            --pool "$pool" --num-workers 1 \
            >> "$LOG_DIR/task-worker-${pool}-${i}.log" 2>&1 &
    done
done

for i in 1 2; do
    $PY $MAIN saga-worker $WORKER_ARGS --max-concurrent 4 >> "$LOG_DIR/saga-worker-${i}.log" 2>&1 &
done

# PR-33 Phase 3: --check-interval removed from both workers. HealthWorker
# reads ServiceConfig.HEALTH_CHECK_INTERVAL_SECONDS; SchedulerWorker reads
# ServiceConfig.SCHEDULER_POLL_INTERVAL_SECONDS. To change cadence during
# an incident: edit services.json and restart the worker. The
# log_startup_snapshot line in each worker's log proves which value
# actually took effect.
$PY $MAIN health $WORKER_ARGS --task-timeout 3600 --saga-timeout 3600 >> "$LOG_DIR/health.log" 2>&1 &
$PY $MAIN scheduler \
    --gateway-url "$GW_URL" \
    --business-url "$BIZ_URL" \
    --queue-service-url "$QS_URL" \
    --cortex-url "$CORTEX_URL" \
    --data-dir "$DATA_DIR" \
    >> "$LOG_DIR/scheduler.log" 2>&1 &

# ── Dispatch Subscriber (PR-34 34d, 2026-04-20) ──────────────────────────────
# Standalone subprocess launched ONLY when
# services.json → runtime_switches.subscriber_enabled is true. Pre-34d the
# subscriber ran as an asyncio task inside the Business FastAPI lifespan;
# it died silently on first uncaught exception and the outbox stopped
# draining without any external signal. Hoisting it out means death is
# now visible via `ps aux | grep main_subscriber` and a stale subscriber
# can no longer take Business API traffic down with it.
#
# The runtime_switches.subscriber_enabled read uses the same _cfg helper
# as the secrets block above. Flip the switch: edit services.json + run
# `bash $0 --stop && bash $0` on the target host. The
# log_startup_snapshot() line in the new subscriber log file
# (subscriber-YYYYMMDD.log) is the audit trail.
SUBSCRIBER_ENABLED=$(_cfg "['runtime_switches']['subscriber_enabled']")
if [ "$SUBSCRIBER_ENABLED" = "True" ]; then
    PYTHONPATH="$BASE/Entangled/packages/server-python:$BASE/novaic-common:$BASE/novaic-business:${PYTHONPATH:-}" \
    # PR-20 (2026-04-20): --cortex-url enables the buffered-dispatch
    # trace-append path (scope.meta.input_message_ids). Subscriber
    # soft-fails on Cortex transport errors — never blocks the core
    # outbox drain — so passing this URL is safe even during Cortex
    # restarts.
    $(py novaic-gateway) "$BASE/novaic-business/main_subscriber.py" \
        --data-dir "$DATA_DIR" \
        --entangled-url "$ENTANGLED_URL" \
        --business-url "$BIZ_URL" \
        --queue-service-url "$QS_URL" \
        --cortex-url "$CORTEX_URL" \
        >> "$LOG_DIR/subscriber.log" 2>&1 &
    echo "  Subscriber: enabled (subprocess pid $!, logs: $LOG_DIR/subscriber-*.log)"
else
    echo "  Subscriber: disabled (runtime_switches.subscriber_enabled=False)"
fi

echo "All backends started. Logs: $LOG_DIR"
