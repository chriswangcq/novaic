#!/bin/bash
# 启动所有服务：Gateway + Queue Service + Workers

set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

CONFIG_FILE="$SCRIPT_DIR/config/services.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: config file not found: $CONFIG_FILE"
    exit 1
fi

eval "$(python3 - <<'PY'
import json
import pathlib
import shlex

cfg = json.loads(pathlib.Path("config/services.json").read_text(encoding="utf-8"))
vals = {
    "NOVAIC_DATA_DIR": cfg["paths"]["data_dir"],
    "RO_HOST": cfg["services"]["runtime_orchestrator"]["host"],
    "RO_PORT": cfg["services"]["runtime_orchestrator"]["port"],
    "RO_URL": cfg["services"]["runtime_orchestrator"]["url"],
    "GATEWAY_HOST": cfg["services"]["gateway"]["host"],
    "GATEWAY_PORT": cfg["services"]["gateway"]["port"],
    "GATEWAY_URL": cfg["services"]["gateway"]["url"],
    "QUEUE_HOST": cfg["services"]["queue_service"]["host"],
    "QUEUE_PORT": cfg["services"]["queue_service"]["port"],
    "QUEUE_URL": cfg["services"]["queue_service"]["url"],
    "TOOLS_HOST": cfg["services"]["tools_server"]["host"],
    "TOOLS_PORT": cfg["services"]["tools_server"]["port"],
    "TOOLS_URL": cfg["services"]["tools_server"]["url"],
    "VMCONTROL_URL": cfg["services"]["vmcontrol"]["url"],
    "FILE_SERVICE_URL": cfg["services"]["file_service"]["url"],
    "TOOL_RESULT_SERVICE_URL": cfg["services"]["tool_result_service"]["url"],
    "NUM_WORKERS": cfg["worker"]["num_workers"],
}
for key, value in vals.items():
    print(f"{key}={shlex.quote(str(value))}")
PY
)"

echo "🚀 Starting NovAIC Services..."
echo "📁 Data directory (from config/services.json): $NOVAIC_DATA_DIR"
echo ""

# 创建日志目录
mkdir -p "$NOVAIC_DATA_DIR/logs"

wait_for_health() {
    local url="$1"
    local name="$2"
    local attempts="${3:-30}"
    local sleep_s=1
    for _ in $(seq 1 "$attempts"); do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "   ✅ $name started successfully"
            return 0
        fi
        sleep "$sleep_s"
    done
    echo "   ❌ $name failed health check: $url"
    return 1
}

# ==================== 启动 Runtime Orchestrator ====================
echo "1️⃣  Starting Runtime Orchestrator ($RO_HOST:$RO_PORT)..."
venv/bin/python3 main_novaic.py runtime-orchestrator --host "$RO_HOST" --port "$RO_PORT" --data-dir "$NOVAIC_DATA_DIR" > "$NOVAIC_DATA_DIR/logs/runtime-orchestrator.log" 2>&1 &
RO_PID=$!
echo "   Runtime Orchestrator PID: $RO_PID"
wait_for_health "$RO_URL/api/health" "Runtime Orchestrator" 60

# ==================== 启动 Gateway ====================
echo ""
echo "2️⃣  Starting Gateway ($GATEWAY_HOST:$GATEWAY_PORT)..."
venv/bin/python3 main_novaic.py gateway --host "$GATEWAY_HOST" --port "$GATEWAY_PORT" --data-dir "$NOVAIC_DATA_DIR" --runtime-orchestrator-url "$RO_URL" --queue-service-url "$QUEUE_URL" --tools-server-url "$TOOLS_URL" --vmcontrol-url "$VMCONTROL_URL" --file-service-url "$FILE_SERVICE_URL" --tool-result-service-url "$TOOL_RESULT_SERVICE_URL" > "$NOVAIC_DATA_DIR/logs/gateway.log" 2>&1 &
GATEWAY_PID=$!
echo "   Gateway PID: $GATEWAY_PID"
wait_for_health "$GATEWAY_URL/api/health" "Gateway" 60

# ==================== 启动 Tools Server ====================
echo ""
echo "3️⃣  Starting Tools Server ($TOOLS_HOST:$TOOLS_PORT)..."
venv/bin/python3 main_novaic.py tools-server --host "$TOOLS_HOST" --port "$TOOLS_PORT" --data-dir "$NOVAIC_DATA_DIR" --gateway-url "$GATEWAY_URL" > "$NOVAIC_DATA_DIR/logs/tools-server.log" 2>&1 &
TOOLS_PID=$!
echo "   Tools Server PID: $TOOLS_PID"
wait_for_health "$TOOLS_URL/api/health" "Tools Server" 60

# ==================== 启动 Queue Service ====================
echo ""
echo "4️⃣  Starting Queue Service ($QUEUE_HOST:$QUEUE_PORT)..."
venv/bin/python3 main_novaic.py queue-service --host "$QUEUE_HOST" --port "$QUEUE_PORT" --data-dir "$NOVAIC_DATA_DIR" > "$NOVAIC_DATA_DIR/logs/queue-service.log" 2>&1 &
QUEUE_PID=$!
echo "   Queue Service PID: $QUEUE_PID"
wait_for_health "$QUEUE_URL/health" "Queue Service" 40

# ==================== 启动 Workers ====================
echo ""
echo "5️⃣  Starting Workers..."

# Watchdog
echo "   - Watchdog..."
venv/bin/python3 main_novaic.py watchdog --gateway-url "$GATEWAY_URL" --queue-service-url "$QUEUE_URL" --runtime-orchestrator-url "$RO_URL" --data-dir "$NOVAIC_DATA_DIR" > "$NOVAIC_DATA_DIR/logs/watchdog.log" 2>&1 &
WATCHDOG_PID=$!
echo "     PID: $WATCHDOG_PID"

# Task Worker
echo "   - Task Worker..."
venv/bin/python3 main_novaic.py task-worker --gateway-url "$GATEWAY_URL" --queue-service-url "$QUEUE_URL" --tools-server-url "$TOOLS_URL" --runtime-orchestrator-url "$RO_URL" --num-workers "$NUM_WORKERS" --data-dir "$NOVAIC_DATA_DIR" > "$NOVAIC_DATA_DIR/logs/task-worker.log" 2>&1 &
TASK_WORKER_PID=$!
echo "     PID: $TASK_WORKER_PID"

# Saga Worker
echo "   - Saga Worker..."
venv/bin/python3 main_novaic.py saga-worker --gateway-url "$GATEWAY_URL" --queue-service-url "$QUEUE_URL" --runtime-orchestrator-url "$RO_URL" --max-concurrent 10 --data-dir "$NOVAIC_DATA_DIR" > "$NOVAIC_DATA_DIR/logs/saga-worker.log" 2>&1 &
SAGA_WORKER_PID=$!
echo "     PID: $SAGA_WORKER_PID"

# Health Worker
echo "   - Health Worker..."
venv/bin/python3 main_novaic.py health --gateway-url "$GATEWAY_URL" --queue-service-url "$QUEUE_URL" --runtime-orchestrator-url "$RO_URL" --check-interval 30 --task-timeout 60 --saga-timeout 1800 --data-dir "$NOVAIC_DATA_DIR" > "$NOVAIC_DATA_DIR/logs/health-worker.log" 2>&1 &
HEALTH_WORKER_PID=$!
echo "     PID: $HEALTH_WORKER_PID"

sleep 2

# ==================== 保存 PID ====================
cat > "$NOVAIC_DATA_DIR/pids.txt" <<EOF
runtime_orchestrator=$RO_PID
gateway=$GATEWAY_PID
tools_server=$TOOLS_PID
queue_service=$QUEUE_PID
watchdog=$WATCHDOG_PID
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
echo "   - Runtime Orchestrator: $RO_URL"
echo "   - Gateway:       $GATEWAY_URL"
echo "   - Tools Server:  $TOOLS_URL"
echo "   - Queue Service: $QUEUE_URL"
echo ""
echo "📊 Databases:"
echo "   - Gateway:       $NOVAIC_DATA_DIR/gateway.db"
echo "   - Runtime Orchestrator: $NOVAIC_DATA_DIR/runtime_orchestrator.db"
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
