#!/bin/bash
# 启动服务并发送测试消息
# 用法: ./scripts/test_send_message.sh

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$BACKEND_DIR"

# 使用临时数据目录
export NOVAIC_DATA_DIR="${NOVAIC_DATA_DIR:-$BACKEND_DIR/data_test}"
mkdir -p "$NOVAIC_DATA_DIR/logs"
echo "📁 Data dir: $NOVAIC_DATA_DIR"

# 选择 Python
PYTHON="${PYTHON:-python3}"
if [ -f "venv/bin/python3" ]; then
    PYTHON="venv/bin/python3"
fi

# 清理可能占用的端口
for port in 19999 19997; do
    pid=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo "🛑 Killing process on port $port (PID $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
done

# 1. 启动 Gateway
echo ""
echo "1️⃣  Starting Gateway (19999)..."
$PYTHON main_gateway.py > "$NOVAIC_DATA_DIR/logs/gateway.log" 2>&1 &
GATEWAY_PID=$!
echo "   PID: $GATEWAY_PID"

# 等待 Gateway 就绪
for i in {1..15}; do
    if curl -s http://127.0.0.1:19999/health > /dev/null 2>&1; then
        echo "   ✅ Gateway ready"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "   ❌ Gateway failed to start"
        kill $GATEWAY_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# 2. 启动 Queue Service
echo ""
echo "2️⃣  Starting Queue Service (19997)..."
$PYTHON -m queue_service.main > "$NOVAIC_DATA_DIR/logs/queue-service.log" 2>&1 &
QUEUE_PID=$!
echo "   PID: $QUEUE_PID"

for i in {1..10}; do
    if curl -s http://127.0.0.1:19997/health > /dev/null 2>&1; then
        echo "   ✅ Queue Service ready"
        break
    fi
    [ $i -eq 10 ] && { echo "   ❌ Queue Service failed"; kill $GATEWAY_PID $QUEUE_PID 2>/dev/null; exit 1; }
    sleep 1
done

# 3. 启动 Workers（Task/Saga Worker 使用环境变量，不接受 --gateway-url）
echo ""
echo "3️⃣  Starting Workers..."
export GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:19999}"
export QUEUE_SERVICE_URL="${QUEUE_SERVICE_URL:-http://127.0.0.1:19997}"
$PYTHON main_watchdog.py --gateway-url "$GATEWAY_URL" --queue-service-url "$QUEUE_SERVICE_URL" > "$NOVAIC_DATA_DIR/logs/watchdog.log" 2>&1 &
$PYTHON -m task_queue.workers.task_worker_sync > "$NOVAIC_DATA_DIR/logs/task-worker.log" 2>&1 &
$PYTHON -m task_queue.workers.saga_worker_sync > "$NOVAIC_DATA_DIR/logs/saga-worker.log" 2>&1 &
sleep 2
echo "   ✅ Workers started"

# 4. 创建 Agent 并发送消息
echo ""
echo "4️⃣  Creating agent and sending message..."

# 创建 Agent
AGENT_RESP=$(curl -s -X POST http://127.0.0.1:19999/api/agents \
    -H "Content-Type: application/json" \
    -d '{"name":"TestAgent","model":null}' 2>/dev/null || echo '{}')

AGENT_ID=$(echo "$AGENT_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','') or d.get('agents',[{}])[0].get('id',''))" 2>/dev/null || true)

if [ -z "$AGENT_ID" ]; then
    # 尝试列出已有 agent
    AGENTS=$(curl -s http://127.0.0.1:19999/api/agents 2>/dev/null || echo '{}')
    AGENT_ID=$(echo "$AGENTS" | python3 -c "import sys,json; d=json.load(sys.stdin); a=d.get('agents',[]); print(a[0]['id'] if a else '')" 2>/dev/null || true)
fi

if [ -z "$AGENT_ID" ]; then
    echo "   ⚠️  No agent found, creating with default..."
    AGENT_ID="test-agent-e2e"
fi

echo "   Agent ID: $AGENT_ID"

# 发送消息
MSG_RESP=$(curl -s -X POST http://127.0.0.1:19999/internal/messages \
    -H "Content-Type: application/json" \
    -d "{\"agent_id\":\"$AGENT_ID\",\"type\":\"USER_MESSAGE\",\"content\":\"你好，这是一条测试消息\"}" 2>/dev/null)

echo ""
echo "5️⃣  Message response:"
echo "$MSG_RESP" | python3 -m json.tool 2>/dev/null || echo "$MSG_RESP"

MSG_ID=$(echo "$MSG_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || true)
if [ -n "$MSG_ID" ]; then
    echo ""
    echo "   ✅ Message sent! message_id=$MSG_ID"
    echo "   Watchdog 将处理消息并触发 message_process Saga"
fi

echo ""
echo "📝 Logs: $NOVAIC_DATA_DIR/logs/"
echo "🛑 To stop: kill $GATEWAY_PID $QUEUE_PID"
echo ""
