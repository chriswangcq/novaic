#!/bin/bash

# 切换到同步 Worker 架构
# 停止所有异步 Worker，启动同步 Worker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

NUM_TASK_WORKERS=${1:-5}
GATEWAY_URL=${2:-"http://127.0.0.1:19999"}

echo "============================================"
echo "切换到同步 Worker 架构"
echo "============================================"
echo "Backend Dir: $BACKEND_DIR"
echo "Gateway URL: $GATEWAY_URL"
echo "TaskWorkers: $NUM_TASK_WORKERS"
echo "============================================"
echo

# 1. 停止所有异步 Worker
echo "🛑 停止异步 Worker..."
pkill -f "task_worker_v2" || true
pkill -f "saga_worker_v2" || true
pkill -f "message_worker" || true
pkill -f "health_worker_v2" || true
pkill -f "watchdog" | grep -v "watchdog_sync" || true
sleep 2

# 确认停止
ASYNC_COUNT=$(pgrep -f "worker_v2|message_worker" | wc -l)
if [ $ASYNC_COUNT -gt 0 ]; then
    echo "⚠️  警告：还有 $ASYNC_COUNT 个异步 Worker 在运行"
    echo "    强制停止..."
    pkill -9 -f "worker_v2|message_worker" || true
    sleep 1
fi

echo "✅ 所有异步 Worker 已停止"
echo

# 2. 启动同步 Worker
echo "🚀 启动同步 Worker..."
cd "$BACKEND_DIR"
bash "$SCRIPT_DIR/start_workers_sync.sh" $NUM_TASK_WORKERS "$GATEWAY_URL"

echo
echo "============================================"
echo "✅ 切换完成！"
echo "============================================"
echo
echo "验证命令："
echo "  ps aux | grep -E 'worker_sync'"
echo
echo "监控日志："
echo "  tail -f $BACKEND_DIR/logs/*.log"
echo
echo "停止所有："
echo "  pkill -f 'worker_sync'"
echo
