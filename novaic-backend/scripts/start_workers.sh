#!/usr/bin/env bash
# 启动多个 Task Worker
# Usage: ./scripts/start_workers.sh [N]  N = Task Worker 数量，默认 5

set -e
NUM_TASK_WORKERS="${1:-5}"
DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/.novaic}"
GATEWAY_URL="${NOVAIC_GATEWAY_URL:-http://127.0.0.1:19999}"
QUEUE_SERVICE_URL="${NOVAIC_QUEUE_SERVICE_URL:-http://127.0.0.1:19997}"
RUNTIME_ORCHESTRATOR_URL="${NOVAIC_RUNTIME_ORCHESTRATOR_URL:-http://127.0.0.1:19993}"
TOOLS_SERVER_URL="${NOVAIC_TOOLS_SERVER_URL:-http://127.0.0.1:19998}"

export NOVAIC_DATA_DIR="$DATA_DIR"
export NOVAIC_GATEWAY_URL="$GATEWAY_URL"
export NOVAIC_QUEUE_SERVICE_URL="$QUEUE_SERVICE_URL"
export NOVAIC_RUNTIME_ORCHESTRATOR_URL="$RUNTIME_ORCHESTRATOR_URL"
export NOVAIC_TOOLS_SERVER_URL="$TOOLS_SERVER_URL"
export PYTHONUNBUFFERED=1

echo "[start_workers] Stopping old workers..."
pkill -f "python main_novaic.py watchdog" 2>/dev/null || true
pkill -f "python main_novaic.py task-worker" 2>/dev/null || true
pkill -f "python main_novaic.py saga-worker" 2>/dev/null || true
pkill -f "python main_novaic.py health" 2>/dev/null || true
sleep 2

echo "[start_workers] Starting $NUM_TASK_WORKERS Task Workers..."
for i in $(seq 1 "$NUM_TASK_WORKERS"); do
  nohup python main_novaic.py task-worker \
    --gateway-url "$GATEWAY_URL" \
    --queue-service-url "$QUEUE_SERVICE_URL" \
    --tools-server-url "$TOOLS_SERVER_URL" \
    --runtime-orchestrator-url "$RUNTIME_ORCHESTRATOR_URL" \
    --num-workers 1 \
    --data-dir "$DATA_DIR" >> /tmp/task_worker_${i}.log 2>&1 &
  echo "  Task Worker $i (PID $!) -> /tmp/task_worker_${i}.log"
done
sleep 1

echo "[start_workers] Starting Saga Worker..."
nohup python main_novaic.py saga-worker \
  --gateway-url "$GATEWAY_URL" \
  --queue-service-url "$QUEUE_SERVICE_URL" \
  --runtime-orchestrator-url "$RUNTIME_ORCHESTRATOR_URL" \
  --max-concurrent "${NOVAIC_MAX_CONCURRENT_SAGAS:-10}" \
  --data-dir "$DATA_DIR" >> /tmp/saga_worker.log 2>&1 &
echo "  Saga Worker (PID $!) -> /tmp/saga_worker.log"

echo "[start_workers] Starting Watchdog..."
nohup python main_novaic.py watchdog \
  --gateway-url "$GATEWAY_URL" \
  --queue-service-url "$QUEUE_SERVICE_URL" \
  --runtime-orchestrator-url "$RUNTIME_ORCHESTRATOR_URL" \
  --data-dir "$DATA_DIR" >> /tmp/watchdog.log 2>&1 &
echo "  Watchdog (PID $!) -> /tmp/watchdog.log"

echo "[start_workers] Starting Health Worker..."
nohup python main_novaic.py health \
  --gateway-url "$GATEWAY_URL" \
  --queue-service-url "$QUEUE_SERVICE_URL" \
  --runtime-orchestrator-url "$RUNTIME_ORCHESTRATOR_URL" \
  --check-interval "${NOVAIC_HEALTH_CHECK_INTERVAL:-10}" \
  --task-timeout "${NOVAIC_TASK_TIMEOUT:-300}" \
  --saga-timeout "${NOVAIC_SAGA_TIMEOUT:-1800}" \
  --data-dir "$DATA_DIR" >> /tmp/health_worker.log 2>&1 &
echo "  Health Worker (PID $!) -> /tmp/health_worker.log"

echo ""
echo "=== Workers started ==="
echo "  Task Workers: $NUM_TASK_WORKERS"
echo "  Logs: /tmp/task_worker_*.log, /tmp/{saga_worker,watchdog,health_worker}.log"
