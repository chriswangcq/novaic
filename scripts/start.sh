#!/usr/bin/env bash
# NovAIC Backend Start Script (Linux/Cloud)
#
# Services:
#   - Gateway       :19999  API + DB + WS
#   - Queue Service  :19997  Task/Saga 队列
#   - File Service   :19995  文件上传/下载
#   - Cortex         :19996  认知基础设施 (Workspace / Recall / Sandbox)
#   - Workers        (watchdog, task-worker ×4, saga-worker ×2, health, scheduler)

set -euo pipefail

BASE="/opt/novaic/services"
DATA_DIR="/opt/novaic/data"
LOG_DIR="$DATA_DIR/logs"
mkdir -p "$LOG_DIR"

PORT_GATEWAY=19999
PORT_QUEUE_SERVICE=19997
PORT_FILE_SERVICE=19995
PORT_CORTEX=19996

GW_URL="http://127.0.0.1:$PORT_GATEWAY"
QS_URL="http://127.0.0.1:$PORT_QUEUE_SERVICE"
FS_URL="http://127.0.0.1:$PORT_FILE_SERVICE"
CORTEX_URL="http://127.0.0.1:$PORT_CORTEX"

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
    pkill -9 -f "main_gateway.py" 2>/dev/null || true
    pkill -9 -f "main_novaic.py" 2>/dev/null || true
    pkill -9 -f "main_file_service.py" 2>/dev/null || true
    pkill -9 -f "main_cortex" 2>/dev/null || true
    # Legacy: kill any leftover RO process from old deployments
    pkill -9 -f "main_runtime_orchestrator.py" 2>/dev/null || true
    sleep 2
    echo "Stopped."
}

[ "${1:-}" = "--stop" ] && stop && exit 0

stop 2>/dev/null || true

for port in $PORT_GATEWAY $PORT_QUEUE_SERVICE $PORT_FILE_SERVICE $PORT_CORTEX; do
    wait_port_free "$port" 8
done

echo "Starting NovAIC backends..."

# Gateway
source /opt/novaic/jwt_secret.env
source /opt/novaic/cortex_oss.env
export JWT_SECRET
$(py novaic-gateway) "$BASE/novaic-gateway/main_gateway.py" \
    --host 127.0.0.1 --port "$PORT_GATEWAY" --data-dir "$DATA_DIR" \
    --queue-service-url "$QS_URL" --file-service-url "$FS_URL" \
    >> "$LOG_DIR/gateway-$(date +%Y%m%d).log" 2>&1 &
wait_port "$PORT_GATEWAY" "Gateway" 30

# Queue Service
$(py novaic-agent-runtime) "$BASE/novaic-agent-runtime/main_novaic.py" queue-service \
    --host 127.0.0.1 --port "$PORT_QUEUE_SERVICE" --data-dir "$DATA_DIR" \
    >> "$LOG_DIR/queue-service.log" 2>&1 &
wait_port "$PORT_QUEUE_SERVICE" "Queue Service"

# File Service
$(py novaic-storage-a) "$BASE/novaic-storage-a/main_file_service.py" \
    --host 127.0.0.1 --port "$PORT_FILE_SERVICE" --data-dir "$DATA_DIR" \
    >> "$LOG_DIR/file-service.log" 2>&1 &
wait_port "$PORT_FILE_SERVICE" "File Service"

# Cortex
source /opt/novaic/cortex_oss.env
export CORTEX_JWT_SECRET="${JWT_SECRET}"
export CORTEX_STORE_ROOT="/opt/novaic/data/cortex"
mkdir -p /opt/novaic/data/cortex
$(py novaic-cortex) -m novaic_cortex.main_cortex \
    >> "$LOG_DIR/cortex.log" 2>&1 &
wait_port "$PORT_CORTEX" "Cortex"

# Workers
PY=$(py novaic-agent-runtime)
MAIN="$BASE/novaic-agent-runtime/main_novaic.py"
WORKER_ARGS="--gateway-url $GW_URL --queue-service-url $QS_URL --data-dir $DATA_DIR"

$PY $MAIN watchdog $WORKER_ARGS >> "$LOG_DIR/watchdog.log" 2>&1 &

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

$PY $MAIN health $WORKER_ARGS --check-interval 30 --task-timeout 3600 --saga-timeout 3600 >> "$LOG_DIR/health.log" 2>&1 &
$PY $MAIN scheduler --gateway-url "$GW_URL" --check-interval 10 --data-dir "$DATA_DIR" >> "$LOG_DIR/scheduler.log" 2>&1 &

echo "All backends started. Logs: $LOG_DIR"
