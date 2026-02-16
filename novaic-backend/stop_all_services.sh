#!/bin/bash
# 停止所有服务

set -e

# 检查环境变量
if [ -z "$NOVAIC_DATA_DIR" ]; then
    export NOVAIC_DATA_DIR=~/.novaic
fi

echo "🛑 Stopping all NovAIC services..."

# 读取 PID 文件
PID_FILE="$NOVAIC_DATA_DIR/pids.txt"

if [ -f "$PID_FILE" ]; then
    echo "📋 Reading PIDs from: $PID_FILE"
    
    # 停止所有进程
    while IFS='=' read -r name pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "   Stopping $name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
        fi
    done < "$PID_FILE"
    
    sleep 2
    
    # 强制杀死仍在运行的进程
    while IFS='=' read -r name pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "   Force killing $name (PID: $pid)..."
            kill -9 "$pid" 2>/dev/null || true
        fi
    done < "$PID_FILE"
    
    rm "$PID_FILE"
else
    echo "⚠️  PID file not found, trying to kill by name..."
    
    # 按进程名杀死（兼容旧入口 + main_novaic 子命令）
    pkill -f "main_novaic.py" || true
    sleep 1
    pkill -9 -f "main_novaic.py" || true
    pkill -f "main_gateway.py" || true
    pkill -f "queue_service.main" || true
    pkill -f "task_worker_sync" || true
    pkill -f "saga_worker_sync" || true
    pkill -f "health_worker_sync" || true
    
    sleep 1
fi

echo ""
echo "✅ All services stopped"
echo ""
