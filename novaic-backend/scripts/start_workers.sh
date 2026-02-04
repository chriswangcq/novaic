#!/usr/bin/env bash
# 启动多个 Task Worker
# Usage: ./scripts/start_workers.sh [N]  N = Task Worker 数量，默认 5

set -e
NUM_TASK_WORKERS="${1:-5}"
DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/.novaic}"
GATEWAY_URL="${NOVAIC_GATEWAY_URL:-http://127.0.0.1:19999}"

export NOVAIC_DATA_DIR="$DATA_DIR"
export NOVAIC_GATEWAY_URL="$GATEWAY_URL"
export PYTHONUNBUFFERED=1

echo "[start_workers] Stopping old workers..."
pkill -f "python main_watchdog.py" 2>/dev/null || true
pkill -f "python main_task.py" 2>/dev/null || true
pkill -f "python main_saga.py" 2>/dev/null || true
pkill -f "python main_health.py" 2>/dev/null || true
sleep 2

echo "[start_workers] Starting $NUM_TASK_WORKERS Task Workers..."
for i in $(seq 1 "$NUM_TASK_WORKERS"); do
  nohup python main_task.py >> /tmp/task_worker_${i}.log 2>&1 &
  echo "  Task Worker $i (PID $!) -> /tmp/task_worker_${i}.log"
done
sleep 1

echo "[start_workers] Starting Saga Worker..."
nohup python main_saga.py >> /tmp/saga_worker.log 2>&1 &
echo "  Saga Worker (PID $!) -> /tmp/saga_worker.log"

echo "[start_workers] Starting Watchdog..."
nohup python main_watchdog.py >> /tmp/watchdog.log 2>&1 &
echo "  Watchdog (PID $!) -> /tmp/watchdog.log"

echo "[start_workers] Starting Health Worker..."
nohup python main_health.py >> /tmp/health_worker.log 2>&1 &
echo "  Health Worker (PID $!) -> /tmp/health_worker.log"

echo ""
echo "=== Workers started ==="
echo "  Task Workers: $NUM_TASK_WORKERS"
echo "  Logs: /tmp/task_worker_*.log, /tmp/{saga_worker,watchdog,health_worker}.log"
