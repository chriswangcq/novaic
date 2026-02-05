#!/usr/bin/env bash
# 本地手动启动所有 Backend 服务（与 Tauri 分开跑时用）
# Usage: ./run_gateways.sh [--all]
#   无参数: 只启动 Gateway + Tools Server
#   --all:  启动全部 6 个服务

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/Library/Application Support/com.novaic.app}"
GATEWAY_URL="${NOVAIC_GATEWAY_URL:-http://127.0.0.1:19999}"

cd "$SCRIPT_DIR"
export NOVAIC_DATA_DIR="$DATA_DIR"
export NOVAIC_GATEWAY_URL="$GATEWAY_URL"

# 停掉旧进程
echo "[run_gateways] Stopping old processes..."
pkill -f "python main_gateway.py" 2>/dev/null || true
pkill -f "python main_tools.py" 2>/dev/null || true
pkill -f "python main_watchdog.py" 2>/dev/null || true
pkill -f "python main_task.py" 2>/dev/null || true
pkill -f "python main_saga.py" 2>/dev/null || true
pkill -f "python main_health.py" 2>/dev/null || true
sleep 2

# 1. 启动 Gateway (19999)
nohup python main_gateway.py > /tmp/gateway.log 2>&1 &
echo "[run_gateways] Gateway started (PID $!) -> /tmp/gateway.log"
sleep 3

# 2. 启动 Tools Server (19998)
nohup python main_tools.py > /tmp/tools_server.log 2>&1 &
echo "[run_gateways] Tools Server started (PID $!) -> /tmp/tools_server.log"

# 如果指定 --all，启动所有 worker 服务
if [[ "$1" == "--all" ]]; then
    sleep 3
    echo "[run_gateways] Starting worker services..."
    
    # 3. Watchdog: 监控 sending 消息
    nohup python main_watchdog.py > /tmp/watchdog.log 2>&1 &
    echo "[run_gateways] Watchdog started (PID $!) -> /tmp/watchdog.log"
    
    # 4. Task Worker: 通用任务执行器
    nohup python main_task.py > /tmp/task_worker.log 2>&1 &
    echo "[run_gateways] Task Worker started (PID $!) -> /tmp/task_worker.log"
    
    # 5. Saga Worker: Saga 流程编排
    nohup python main_saga.py > /tmp/saga_worker.log 2>&1 &
    echo "[run_gateways] Saga Worker started (PID $!) -> /tmp/saga_worker.log"
    
    # 6. Health Worker: 超时回收
    nohup python main_health.py > /tmp/health_worker.log 2>&1 &
    echo "[run_gateways] Health Worker started (PID $!) -> /tmp/health_worker.log"
fi

sleep 5

# 检查状态
echo ""
echo "=== Gateway (19999) ==="
curl -s "http://127.0.0.1:19999/api/health" | python -m json.tool 2>/dev/null || echo "(not ready)"
echo ""
echo "=== Tools Server (19998) ==="
curl -s "http://127.0.0.1:19998/api/health" | python -m json.tool 2>/dev/null || echo "(not ready)"

echo ""
echo "Logs:"
echo "  Gateway:     tail -f /tmp/gateway.log"
echo "  Tools Server: tail -f /tmp/tools_server.log"
if [[ "$1" == "--all" ]]; then
    echo "  Watchdog:    tail -f /tmp/watchdog.log"
    echo "  Task Worker: tail -f /tmp/task_worker.log"
    echo "  Saga Worker: tail -f /tmp/saga_worker.log"
    echo "  Health:      tail -f /tmp/health_worker.log"
fi
