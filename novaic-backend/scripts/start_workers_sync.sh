#!/bin/bash

# 启动所有同步 Worker（多进程架构）
# 用法：./start_workers_sync.sh [num_task_workers] [gateway_url]

set -e

# 配置
NUM_TASK_WORKERS=${1:-5}
GATEWAY_URL=${2:-"http://127.0.0.1:19999"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# 导出环境变量
export NOVAIC_GATEWAY_URL="$GATEWAY_URL"
export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

# 日志目录
LOG_DIR="$BACKEND_DIR/logs"
mkdir -p "$LOG_DIR"

echo "========================================"
echo "启动同步 Workers (多进程)"
echo "========================================"
echo "Backend Dir: $BACKEND_DIR"
echo "Gateway URL: $GATEWAY_URL"
echo "TaskWorkers: $NUM_TASK_WORKERS"
echo "Log Dir: $LOG_DIR"
echo "========================================"
echo

# 停止旧的 Worker 进程
echo "🛑 停止旧的 Worker 进程..."
pkill -f "task_worker_sync" || true
pkill -f "saga_worker_sync" || true
pkill -f "watchdog_sync" || true
pkill -f "health_worker_sync" || true
sleep 1

# 启动 TaskWorkers（多进程）
echo "🚀 启动 $NUM_TASK_WORKERS 个 TaskWorker (sync)..."
cd "$BACKEND_DIR"
nohup python -m task_queue.workers.task_worker_sync $NUM_TASK_WORKERS \
  > "$LOG_DIR/task_worker_sync.log" 2>&1 &
TASK_WORKER_PID=$!
echo "   TaskWorker PID: $TASK_WORKER_PID"

sleep 0.5

# 启动 SagaWorker（单进程，内部多线程）
echo "🚀 启动 SagaWorker (sync, 10 concurrent)..."
nohup python -m task_queue.workers.saga_worker_sync \
  > "$LOG_DIR/saga_worker_sync.log" 2>&1 &
SAGA_WORKER_PID=$!
echo "   SagaWorker PID: $SAGA_WORKER_PID"

sleep 0.5

# 启动 Watchdog（单进程）
echo "🚀 启动 Watchdog (sync)..."
nohup python -m task_queue.workers.watchdog_sync \
  > "$LOG_DIR/watchdog_sync.log" 2>&1 &
WATCHDOG_PID=$!
echo "   Watchdog PID: $WATCHDOG_PID"

sleep 0.5

# 启动 HealthWorker（单进程）
echo "🚀 启动 HealthWorker (sync)..."
nohup python -m task_queue.workers.health_worker_sync \
  > "$LOG_DIR/health_worker_sync.log" 2>&1 &
HEALTH_WORKER_PID=$!
echo "   HealthWorker PID: $HEALTH_WORKER_PID"

echo
echo "✅ 所有 Worker 已启动（同步模式）"
echo "========================================"
echo "进程清单："
echo "  TaskWorker   : PID $TASK_WORKER_PID (x$NUM_TASK_WORKERS 进程)"
echo "  SagaWorker   : PID $SAGA_WORKER_PID (10 并发线程)"
echo "  Watchdog     : PID $WATCHDOG_PID"
echo "  HealthWorker : PID $HEALTH_WORKER_PID"
echo "========================================"
echo "日志文件："
echo "  TaskWorker   : $LOG_DIR/task_worker_sync.log"
echo "  SagaWorker   : $LOG_DIR/saga_worker_sync.log"
echo "  Watchdog     : $LOG_DIR/watchdog_sync.log"
echo "  HealthWorker : $LOG_DIR/health_worker_sync.log"
echo "========================================"
echo
echo "📊 实时监控命令："
echo "  tail -f $LOG_DIR/*.log"
echo
echo "🛑 停止所有 Worker："
echo "  pkill -f 'task_worker_sync|saga_worker_sync|watchdog_sync|health_worker_sync'"
echo
