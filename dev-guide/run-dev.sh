#!/bin/bash
# NovAIC 开发环境启动脚本 (v22+ / Task Queue v2)
#
# 用法:
#   ./run-dev.sh                  # 启动全部
#   ./run-dev.sh stop             # 停止全部
#   ./run-dev.sh status           # 查看进程状态
#   ./run-dev.sh reset            # 清理运行态数据
#   ./run-dev.sh logs [service]   # tail 日志 (service 可选)
#   ./run-dev.sh gateway|mcp|watchdog|task|saga|health
#
# 约定:
# - 所有服务都使用 /tmp/*.log 日志
# - Gateway/MCP/Workers 都需要 NOVAIC_GATEWAY_URL + NOVAIC_TOOLS_SERVER_URL

set -euo pipefail

# 路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/novaic-backend"

# 端口与环境
GATEWAY_URL="${NOVAIC_GATEWAY_URL:-http://127.0.0.1:19999}"
TOOLS_SERVER_URL="${NOVAIC_TOOLS_SERVER_URL:-http://127.0.0.1:19998}"
export NOVAIC_GATEWAY_URL="$GATEWAY_URL"
export NOVAIC_TOOLS_SERVER_URL="$TOOLS_SERVER_URL"
export NOVAIC_DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/.novaic}"
export PYTHONUNBUFFERED=1

# Worker 数量配置
NUM_TASK_WORKERS="${NOVAIC_TASK_WORKERS:-3}"
NUM_SAGA_WORKERS="${NOVAIC_SAGA_WORKERS:-3}"

# 日志
LOG_DIR="/tmp"
LOG_GATEWAY="$LOG_DIR/gateway.log"
LOG_MCP="$LOG_DIR/mcp.log"
LOG_QUEUE="$LOG_DIR/queue.log"
LOG_WATCHDOG="$LOG_DIR/watchdog.log"
LOG_TASK="$LOG_DIR/task.log"
LOG_SAGA="$LOG_DIR/saga.log"
LOG_HEALTH="$LOG_DIR/health.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

activate_venv() {
    if [ -d "$BACKEND_DIR/venv" ]; then
        source "$BACKEND_DIR/venv/bin/activate"
    else
        log_warn "Virtualenv not found at $BACKEND_DIR/venv, using system python"
    fi
}

ensure_dirs() {
    mkdir -p "$NOVAIC_DATA_DIR"
}

start_process() {
    local name="$1"
    local cmd="$2"
    local log_file="$3"

    log_info "Starting ${name}..."
    (cd "$BACKEND_DIR" && activate_venv && nohup bash -c "$cmd" > "$log_file" 2>&1 &)
}

wait_for_health() {
    local url="$1"
    local name="$2"
    local attempts=20
    local sleep_s=1
    for _ in $(seq 1 "$attempts"); do
        if curl -s "$url" > /dev/null 2>&1; then
            log_info "${name} healthy"
            return 0
        fi
        sleep "$sleep_s"
    done
    log_error "${name} health check failed: $url"
    return 1
}

start_gateway() {
    start_process "Gateway" "python main_gateway.py" "$LOG_GATEWAY"
    wait_for_health "$GATEWAY_URL/api/health" "Gateway"
}

start_mcp() {
    start_process "Tools Server" "python main_tools.py" "$LOG_MCP"
    wait_for_health "$TOOLS_SERVER_URL/api/health" "Tools Server"
}

start_queue() {
    start_process "Queue Service" "PYTHONPATH=. python queue_service/main.py" "$LOG_QUEUE"
    wait_for_health "http://127.0.0.1:19997/health" "Queue Service"
}

start_watchdog() { start_process "Watchdog" "python main_watchdog.py" "$LOG_WATCHDOG"; }
start_health()   { start_process "Health Worker" "python main_health.py" "$LOG_HEALTH"; }

start_task() {
    log_info "Starting $NUM_TASK_WORKERS Task Workers..."
    for i in $(seq 1 "$NUM_TASK_WORKERS"); do
        local log_file="$LOG_DIR/task-$i.log"
        (cd "$BACKEND_DIR" && activate_venv && nohup bash -c "python main_task.py" > "$log_file" 2>&1 &)
    done
}

start_saga() {
    log_info "Starting $NUM_SAGA_WORKERS Saga Workers..."
    for i in $(seq 1 "$NUM_SAGA_WORKERS"); do
        local log_file="$LOG_DIR/saga-$i.log"
        (cd "$BACKEND_DIR" && activate_venv && nohup bash -c "python main_saga.py" > "$log_file" 2>&1 &)
    done
}

start_workers() {
    start_watchdog
    start_task
    start_saga
    start_health
}

stop_all() {
    log_info "Stopping all services..."
    pkill -f "python.*main_gateway.py" 2>/dev/null || true
    pkill -f "python.*main_tools.py" 2>/dev/null || true
    pkill -f "python.*queue_service/main.py" 2>/dev/null || true
    pkill -f "python.*main_watchdog.py" 2>/dev/null || true
    pkill -f "python.*main_task.py" 2>/dev/null || true
    pkill -f "python.*main_saga.py" 2>/dev/null || true
    pkill -f "python.*main_health.py" 2>/dev/null || true
    log_info "All services stopped"
}

reset_runtime_data() {
    log_warn "Resetting runtime data (tq_tasks/tq_sagas/agent_runtimes/chat_messages)..."
    sqlite3 "$NOVAIC_DATA_DIR/novaic.db" "
DELETE FROM agent_runtimes;
DELETE FROM tq_sagas;
DELETE FROM tq_tasks;
DELETE FROM chat_messages;
UPDATE subagents SET status = 'sleeping';
"
    log_info "Runtime data reset complete"
}

show_status() {
    echo "=== Running Services ==="
    local gateway_count=$(pgrep -f "python.*main_gateway.py" 2>/dev/null | wc -l | tr -d ' ')
    local mcp_count=$(pgrep -f "python.*main_tools.py" 2>/dev/null | wc -l | tr -d ' ')
    local queue_count=$(pgrep -f "python.*queue_service/main.py" 2>/dev/null | wc -l | tr -d ' ')
    local watchdog_count=$(pgrep -f "python.*main_watchdog.py" 2>/dev/null | wc -l | tr -d ' ')
    local task_count=$(pgrep -f "python.*main_task.py" 2>/dev/null | wc -l | tr -d ' ')
    local saga_count=$(pgrep -f "python.*main_saga.py" 2>/dev/null | wc -l | tr -d ' ')
    local health_count=$(pgrep -f "python.*main_health.py" 2>/dev/null | wc -l | tr -d ' ')
    
    echo "Gateway:       $gateway_count"
    echo "Tools Server:  $mcp_count"
    echo "Queue Service: $queue_count"
    echo "Watchdog:      $watchdog_count"
    echo "Task Workers:  $task_count (configured: $NUM_TASK_WORKERS)"
    echo "Saga Workers:  $saga_count (configured: $NUM_SAGA_WORKERS)"
    echo "Health Worker: $health_count"
}

tail_logs() {
    local target="${1:-all}"
    case "$target" in
        gateway) tail -n 50 "$LOG_GATEWAY" ;;
        mcp) tail -n 50 "$LOG_MCP" ;;
        watchdog) tail -n 50 "$LOG_WATCHDOG" ;;
        task) tail -n 50 "$LOG_TASK" ;;
        saga) tail -n 50 "$LOG_SAGA" ;;
        health) tail -n 50 "$LOG_HEALTH" ;;
        all|*)
            tail -n 50 "$LOG_GATEWAY" "$LOG_MCP" "$LOG_WATCHDOG" "$LOG_TASK" "$LOG_SAGA" "$LOG_HEALTH"
            ;;
    esac
}

show_help() {
    cat <<'EOF'
NovAIC Development Environment (v22+)

Usage: ./run-dev.sh [command]

Commands:
  (none)        Start all services
  gateway       Start Gateway only
  mcp           Start Tools Server only
  watchdog      Start Watchdog only
  task          Start Task Worker only
  saga          Start Saga Worker only
  health        Start Health Worker only
  workers       Start Watchdog/Task/Saga/Health
  stop          Stop all services
  status        Show running processes
  reset         Clear runtime data (tq_tasks/tq_sagas/agent_runtimes/chat_messages)
  logs [name]   Tail logs (gateway|mcp|watchdog|task|saga|health|all)
  help          Show this help

Environment:
  NOVAIC_DATA_DIR        Data directory (default: ~/.novaic)
  NOVAIC_GATEWAY_URL     Gateway URL (default: http://127.0.0.1:19999)
  NOVAIC_TOOLS_SERVER_URL Tools Server URL (default: http://127.0.0.1:19998)
  NOVAIC_TASK_WORKERS    Number of Task Workers (default: 3)
  NOVAIC_SAGA_WORKERS    Number of Saga Workers (default: 3)
EOF
}

ensure_dirs

case "${1:-all}" in
    gateway)  start_gateway ;;
    mcp|mcp-gateway|tools) start_mcp ;;
    watchdog|monitor) start_watchdog ;;
    task)     start_task ;;
    saga)     start_saga ;;
    health)   start_health ;;
    workers)  start_workers ;;
    stop)     stop_all ;;
    status)   show_status ;;
    reset)    reset_runtime_data ;;
    logs)     tail_logs "${2:-all}" ;;
    help|--help|-h) show_help ;;
    queue)    start_queue ;;
    all|"")
        start_gateway
        start_mcp
        start_queue
        start_workers
        log_info "All services started"
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
