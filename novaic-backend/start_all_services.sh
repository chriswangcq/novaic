#!/bin/bash
# 启动所有服务：Gateway + Queue Service + Workers

set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查环境变量
if [ -z "$NOVAIC_DATA_DIR" ]; then
    echo "❌ Error: NOVAIC_DATA_DIR environment variable is not set"
    echo "Please set it to your data directory, e.g.:"
    echo "  export NOVAIC_DATA_DIR=~/.novaic"
    exit 1
fi

echo "🚀 Starting NovAIC Services..."
echo "📁 Data directory: $NOVAIC_DATA_DIR"
echo ""

# 创建日志目录
mkdir -p "$NOVAIC_DATA_DIR/logs"

# ==================== 启动 Gateway ====================
echo "1️⃣  Starting Gateway (port 19999)..."
venv/bin/python3 main_gateway.py > "$NOVAIC_DATA_DIR/logs/gateway.log" 2>&1 &
GATEWAY_PID=$!
echo "   Gateway PID: $GATEWAY_PID"
sleep 2

# 检查 Gateway 是否启动成功
if curl -s http://127.0.0.1:19999/health > /dev/null 2>&1; then
    echo "   ✅ Gateway started successfully"
else
    echo "   ⚠️  Gateway may not be ready yet"
fi

# ==================== 启动 Queue Service ====================
echo ""
echo "2️⃣  Starting Queue Service (port 19997)..."
venv/bin/python3 -m queue_service.main > "$NOVAIC_DATA_DIR/logs/queue-service.log" 2>&1 &
QUEUE_PID=$!
echo "   Queue Service PID: $QUEUE_PID"
sleep 2

# 检查 Queue Service 是否启动成功
if curl -s http://127.0.0.1:19997/health > /dev/null 2>&1; then
    echo "   ✅ Queue Service started successfully"
else
    echo "   ⚠️  Queue Service may not be ready yet"
fi

# ==================== 启动 Workers ====================
echo ""
echo "3️⃣  Starting Workers..."

# Task Worker
echo "   - Task Worker..."
venv/bin/python3 -m task_queue.workers.task_worker_sync 2 > "$NOVAIC_DATA_DIR/logs/task-worker.log" 2>&1 &
TASK_WORKER_PID=$!
echo "     PID: $TASK_WORKER_PID"

# Saga Worker
echo "   - Saga Worker..."
venv/bin/python3 -m task_queue.workers.saga_worker_sync 1 > "$NOVAIC_DATA_DIR/logs/saga-worker.log" 2>&1 &
SAGA_WORKER_PID=$!
echo "     PID: $SAGA_WORKER_PID"

# Health Worker
echo "   - Health Worker..."
venv/bin/python3 -m task_queue.workers.health_worker_sync > "$NOVAIC_DATA_DIR/logs/health-worker.log" 2>&1 &
HEALTH_WORKER_PID=$!
echo "     PID: $HEALTH_WORKER_PID"

sleep 2

# ==================== 保存 PID ====================
cat > "$NOVAIC_DATA_DIR/pids.txt" <<EOF
gateway=$GATEWAY_PID
queue_service=$QUEUE_PID
task_worker=$TASK_WORKER_PID
saga_worker=$SAGA_WORKER_PID
health_worker=$HEALTH_WORKER_PID
EOF

echo ""
echo "✅ All services started!"
echo ""
echo "📋 Process IDs saved to: $NOVAIC_DATA_DIR/pids.txt"
echo ""
echo "🔍 Service URLs:"
echo "   - Gateway:       http://127.0.0.1:19999"
echo "   - Queue Service: http://127.0.0.1:19997"
echo ""
echo "📊 Databases:"
echo "   - Gateway:       $NOVAIC_DATA_DIR/novaic.db"
echo "   - Queue Service: $NOVAIC_DATA_DIR/queue.db"
echo ""
echo "📝 Logs:"
echo "   - Gateway:       $NOVAIC_DATA_DIR/logs/gateway.log"
echo "   - Queue Service: $NOVAIC_DATA_DIR/logs/queue-service.log"
echo "   - Task Worker:   $NOVAIC_DATA_DIR/logs/task-worker.log"
echo "   - Saga Worker:   $NOVAIC_DATA_DIR/logs/saga-worker.log"
echo "   - Health Worker: $NOVAIC_DATA_DIR/logs/health-worker.log"
echo ""
echo "🛑 To stop all services:"
echo "   ./stop_all_services.sh"
echo ""
