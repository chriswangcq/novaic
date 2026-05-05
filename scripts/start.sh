#!/usr/bin/env bash
# NovAIC Backend Start Script (Linux/Cloud)
#
# Configuration:
#   services.json = code-shipped defaults + secrets
#   runtime_switches overlay = /opt/novaic/etc/runtime_switches.json
#   CLI args = process-local bind/path overrides (visible in ps aux)
#   Zero exports — all config passed as CLI args or read through strict_config.
#
# Services:
#   - Entangled      :19900  Entity CRUD (single source of truth) + WS Sync
#   - Gateway        :19999  Auth, App WS signaling, log broadcast, Blob edge
#   - Business       :19998  All /internal/* APIs, Entangled action hooks, schema push
#   - Device         :19993  PC bridge WS, VM lifecycle, SSH key mgmt, WebRTC signaling
#   - Queue Service  :19997  Task/Saga queue management
#   - Blob Service   :19995  Blob upload/download
#   - Cortex         :19996  Scope tree, LLM context assembly, Workspace, Sandbox
#   - Workers        task-worker ×4, saga-worker ×2, health ×1, scheduler ×1
#
# Communication:
#   Workers → Business  (/internal/* calls, including entity proxy)
#   Workers → Gateway   (only /api/logs/broadcast for WS push)
#   Workers → Cortex    (scope/context/shell APIs)
#   Entangled → Business (action hook callbacks)
#   Business → Entangled (schema push, entity proxy, action hook handling)
#   Subscriber → Entangled (Environment notification drain, required)
#   Gateway → App       (Entangled sync endpoint discovery only)
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
PORT_BLOB_SERVICE=19995
PORT_DEVICE=19993

# ── Derived URLs (used only as CLI arg values below) ─────────────────────────

ENTANGLED_URL="http://$HOST:$PORT_ENTANGLED"
GW_URL="http://$HOST:$PORT_GATEWAY"
BIZ_URL="http://$HOST:$PORT_BUSINESS"
QS_URL="http://$HOST:$PORT_QUEUE_SERVICE"
BLOB_URL="http://$HOST:$PORT_BLOB_SERVICE"
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

kill_port_owner() {
    local port="$1"
    local pids
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
    [ -z "$pids" ] && return 0
    kill -9 $pids 2>/dev/null || true
}

stop() {
    pkill -TERM -f "main_subscriber.py" 2>/dev/null || true
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
    pkill -9 -f "main_blob_service.py" 2>/dev/null || true
    pkill -9 -f "main_cortex" 2>/dev/null || true
    for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_CORTEX; do
        kill_port_owner "$port"
    done
    sleep 2
    echo "Stopped."
}

[ "${1:-}" = "--stop" ] && stop && exit 0

stop 2>/dev/null || true

for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_CORTEX; do
    wait_port_free "$port" 8
done

echo "Starting NovAIC backends..."

# ── Secrets (read from services.json, pass as CLI args) ──────────────────────
#
# TD-5/PR-101: use the exact same strict_config loader as Python services.
# Do not reimplement runtime_switches overlay semantics in shell: the loader
# owns env/sibling/prod overlay precedence, unknown-key validation, and
# required-key fail-fast behavior.
_cfg() { PYTHONPATH="$BASE/novaic-common:${PYTHONPATH:-}" python3 - "$1" <<PYEOF
import sys
from common.strict_config import load_services_config

path_expr = sys.argv[1]
cfg = load_services_config("$BASE/novaic-common/config/services.json", force_reload=True)
print(eval("cfg.raw" + path_expr))
PYEOF
}

JWT_SECRET=$(_cfg "['secrets']['jwt_secret']")
OSS_AK=$(_cfg "['secrets']['alibaba_cloud_access_key_id']")
OSS_SK=$(_cfg "['secrets']['alibaba_cloud_access_key_secret']")
BLOB_OSS_ENDPOINT=$(_cfg "['blob_storage']['oss_endpoint']")
BLOB_OSS_REGION=$(_cfg "['blob_storage']['oss_region']")
BLOB_OSS_BUCKET=$(_cfg "['blob_storage']['oss_bucket']")
CORTEX_INTERNAL_KEY=$(_cfg "['secrets']['cortex_internal_key']")

# ── Services (all config passed as explicit CLI args — no exports) ───────────

PYTHONPATH="$BASE/Entangled/packages/server-python:${PYTHONPATH:-}" \
$(py novaic-gateway) -m entangled.app.main \
    --host "$HOST" --port "$PORT_ENTANGLED" \
    --db-path "$DATA_DIR/entangled.db" \
    --service-token "$JWT_SECRET" \
    >> "$LOG_DIR/entangled.log" 2>&1 &
wait_port "$PORT_ENTANGLED" "Entangled Service"

PYTHONPATH="$BASE/novaic-common:${PYTHONPATH:-}" \
$(py novaic-gateway) "$BASE/novaic-gateway/main_gateway.py" \
    --host "$HOST" --port "$PORT_GATEWAY" --data-dir "$DATA_DIR" \
    --queue-service-url "$QS_URL" --blob-service-url "$BLOB_URL" \
    --blob-upload-url "$BLOB_URL" \
    >> "$LOG_DIR/gateway-$(date +%Y%m%d).log" 2>&1 &
wait_port "$PORT_GATEWAY" "Gateway" 30

PYTHONPATH="$BASE/Entangled/packages/server-python:$BASE/novaic-common:$BASE/novaic-business:${PYTHONPATH:-}" \
$(py novaic-gateway) "$BASE/novaic-business/main_business.py" \
    --host "$HOST" --port "$PORT_BUSINESS" --data-dir "$DATA_DIR" \
    --entangled-url "$ENTANGLED_URL" --gateway-url "$GW_URL" \
    >> "$LOG_DIR/business-$(date +%Y%m%d).log" 2>&1 &
wait_port "$PORT_BUSINESS" "Business Service"
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

NOVAIC_BLOB_BACKEND=oss \
NOVAIC_OSS_ACCESS_KEY="$OSS_AK" \
NOVAIC_OSS_SECRET_KEY="$OSS_SK" \
NOVAIC_OSS_ENDPOINT="$BLOB_OSS_ENDPOINT" \
NOVAIC_OSS_REGION="$BLOB_OSS_REGION" \
NOVAIC_OSS_BUCKET="$BLOB_OSS_BUCKET" \
AWS_DEFAULT_REGION="$BLOB_OSS_REGION" \
PYTHONPATH="$BASE/novaic-common:${PYTHONPATH:-}" \
$(py novaic-blob-service) "$BASE/novaic-blob-service/main_blob_service.py" \
    --host "$HOST" --port "$PORT_BLOB_SERVICE" --data-dir "$DATA_DIR" \
    >> "$LOG_DIR/blob-service.log" 2>&1 &
wait_port "$PORT_BLOB_SERVICE" "Blob Service"

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
CORTEX_BLOB_SERVICE_URL="$BLOB_URL" \
PYTHONPATH="$BASE/novaic-cortex:$BASE/novaic-common:${PYTHONPATH:-}" \
$(py novaic-cortex) -m novaic_cortex.main_cortex \
    --host "$HOST" --port "$PORT_CORTEX" \
    --jwt-secret "$JWT_SECRET" \
    --internal-key "$CORTEX_INTERNAL_KEY" \
    --blob-service-url "$BLOB_URL" \
    --scope-state-log-path "$DATA_DIR/cortex/scope_state_transitions.ndjson" \
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
$PY $MAIN health \
    --queue-service-url "$QS_URL" \
    --data-dir "$DATA_DIR" \
    --task-timeout 3600 \
    --saga-timeout 3600 \
    >> "$LOG_DIR/health.log" 2>&1 &
$PY $MAIN scheduler \
    --gateway-url "$GW_URL" \
    --business-url "$BIZ_URL" \
    --queue-service-url "$QS_URL" \
    --cortex-url "$CORTEX_URL" \
    --data-dir "$DATA_DIR" \
    >> "$LOG_DIR/scheduler.log" 2>&1 &

# ── Dispatch Subscriber ──────────────────────────────────────────────────────
# Required Environment notification drain. It is a standalone subprocess so a
# failed drain loop is visible as a missing process instead of being hidden
# inside Business's FastAPI lifespan.
PYTHONPATH="$BASE/Entangled/packages/server-python:$BASE/novaic-common:$BASE/novaic-business:${PYTHONPATH:-}" \
$(py novaic-gateway) "$BASE/novaic-business/main_subscriber.py" \
    --data-dir "$DATA_DIR" \
    --entangled-url "$ENTANGLED_URL" \
    --business-url "$BIZ_URL" \
    --queue-service-url "$QS_URL" \
    >> "$LOG_DIR/subscriber.log" 2>&1 &
echo "  Subscriber: required (subprocess pid $!, logs: $LOG_DIR/subscriber-*.log)"

echo "All backends started. Logs: $LOG_DIR"
