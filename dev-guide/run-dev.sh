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
# - 所有服务通过 main_novaic.py 子命令启动并使用显式 CLI 参数

set -euo pipefail

# 路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/novaic-backend"

# Strict single-file config
CONFIG_JSON="$BACKEND_DIR/config/services.json"
if [ ! -f "$CONFIG_JSON" ]; then
    log_error "Missing strict config file: $CONFIG_JSON"
    exit 1
fi

eval "$(CONFIG_JSON_PATH="$CONFIG_JSON" python3 - <<'PY'
import json
import os
import shlex
from pathlib import Path

cfg_path = Path(os.environ["CONFIG_JSON_PATH"])
cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
vals = {
    "GATEWAY_HOST": cfg["services"]["gateway"]["host"],
    "GATEWAY_PORT": cfg["services"]["gateway"]["port"],
    "GATEWAY_URL": cfg["services"]["gateway"]["url"],
    "TOOLS_SERVER_HOST": cfg["services"]["tools_server"]["host"],
    "TOOLS_SERVER_PORT": cfg["services"]["tools_server"]["port"],
    "TOOLS_SERVER_URL": cfg["services"]["tools_server"]["url"],
    "QUEUE_SERVICE_HOST": cfg["services"]["queue_service"]["host"],
    "QUEUE_SERVICE_PORT": cfg["services"]["queue_service"]["port"],
    "QUEUE_SERVICE_URL": cfg["services"]["queue_service"]["url"],
    "RUNTIME_ORCHESTRATOR_HOST": cfg["services"]["runtime_orchestrator"]["host"],
    "RUNTIME_ORCHESTRATOR_PORT": cfg["services"]["runtime_orchestrator"]["port"],
    "RUNTIME_ORCHESTRATOR_URL": cfg["services"]["runtime_orchestrator"]["url"],
    "VMCONTROL_URL": cfg["services"]["vmcontrol"]["url"],
    "FILE_SERVICE_URL": cfg["services"]["file_service"]["url"],
    "TOOL_RESULT_SERVICE_URL": cfg["services"]["tool_result_service"]["url"],
    "NOVAIC_DATA_DIR": cfg["paths"]["data_dir"],
    "NUM_TASK_WORKERS": cfg["worker"]["num_workers"],
}
for key, value in vals.items():
    print(f"{key}={shlex.quote(str(value))}")
PY
)"
NUM_SAGA_WORKERS="$NUM_TASK_WORKERS"
export PYTHONUNBUFFERED=1

# 日志
LOG_DIR="/tmp"
LOG_RO="$LOG_DIR/runtime-orchestrator.log"
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
    local attempts="${3:-20}"
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
    start_process "Gateway" \
      "python main_novaic.py gateway --host $GATEWAY_HOST --port $GATEWAY_PORT --data-dir '$NOVAIC_DATA_DIR' --runtime-orchestrator-url '$RUNTIME_ORCHESTRATOR_URL' --queue-service-url '$QUEUE_SERVICE_URL' --tools-server-url '$TOOLS_SERVER_URL' --vmcontrol-url '$VMCONTROL_URL' --file-service-url '$FILE_SERVICE_URL' --tool-result-service-url '$TOOL_RESULT_SERVICE_URL'" \
      "$LOG_GATEWAY"
    wait_for_health "$GATEWAY_URL/api/health" "Gateway"
}

start_mcp() {
    start_process "Tools Server" \
      "python main_novaic.py tools-server --host $TOOLS_SERVER_HOST --port $TOOLS_SERVER_PORT --data-dir '$NOVAIC_DATA_DIR' --gateway-url '$GATEWAY_URL'" \
      "$LOG_MCP"
    # Tools Server may need longer startup when restoring runtimes.
    wait_for_health "$TOOLS_SERVER_URL/api/health" "Tools Server" 45
}

start_queue() {
    start_process "Queue Service" \
      "python main_novaic.py queue-service --host $QUEUE_SERVICE_HOST --port $QUEUE_SERVICE_PORT --data-dir '$NOVAIC_DATA_DIR'" \
      "$LOG_QUEUE"
    wait_for_health "$QUEUE_SERVICE_URL/health" "Queue Service"
}

start_runtime_orchestrator() {
    start_process "Runtime Orchestrator" \
      "python main_novaic.py runtime-orchestrator --host $RUNTIME_ORCHESTRATOR_HOST --port $RUNTIME_ORCHESTRATOR_PORT --data-dir '$NOVAIC_DATA_DIR'" \
      "$LOG_RO"
    wait_for_health "$RUNTIME_ORCHESTRATOR_URL/api/health" "Runtime Orchestrator"
}

start_watchdog() {
    start_process "Watchdog" \
      "python main_novaic.py watchdog --gateway-url '$GATEWAY_URL' --queue-service-url '$QUEUE_SERVICE_URL' --runtime-orchestrator-url '$RUNTIME_ORCHESTRATOR_URL' --data-dir '$NOVAIC_DATA_DIR'" \
      "$LOG_WATCHDOG"
}

start_health() {
    start_process "Health Worker" \
      "python main_novaic.py health --gateway-url '$GATEWAY_URL' --queue-service-url '$QUEUE_SERVICE_URL' --runtime-orchestrator-url '$RUNTIME_ORCHESTRATOR_URL' --check-interval 30 --task-timeout 60 --saga-timeout 1800 --data-dir '$NOVAIC_DATA_DIR'" \
      "$LOG_HEALTH"
}

start_task() {
    log_info "Starting $NUM_TASK_WORKERS Task Workers..."
    for i in $(seq 1 "$NUM_TASK_WORKERS"); do
        local log_file="$LOG_DIR/task-$i.log"
        (cd "$BACKEND_DIR" && activate_venv && nohup bash -c "python main_novaic.py task-worker --gateway-url '$GATEWAY_URL' --queue-service-url '$QUEUE_SERVICE_URL' --tools-server-url '$TOOLS_SERVER_URL' --runtime-orchestrator-url '$RUNTIME_ORCHESTRATOR_URL' --num-workers $NUM_TASK_WORKERS --data-dir '$NOVAIC_DATA_DIR'" > "$log_file" 2>&1 &)
    done
}

start_saga() {
    log_info "Starting $NUM_SAGA_WORKERS Saga Workers..."
    for i in $(seq 1 "$NUM_SAGA_WORKERS"); do
        local log_file="$LOG_DIR/saga-$i.log"
        (cd "$BACKEND_DIR" && activate_venv && nohup bash -c "python main_novaic.py saga-worker --gateway-url '$GATEWAY_URL' --queue-service-url '$QUEUE_SERVICE_URL' --runtime-orchestrator-url '$RUNTIME_ORCHESTRATOR_URL' --max-concurrent 10 --data-dir '$NOVAIC_DATA_DIR'" > "$log_file" 2>&1 &)
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
    pkill -f "python.*main_novaic.py runtime-orchestrator" 2>/dev/null || true
    pkill -f "python.*main_novaic.py gateway" 2>/dev/null || true
    pkill -f "python.*main_novaic.py tools-server" 2>/dev/null || true
    pkill -f "python.*main_novaic.py queue-service" 2>/dev/null || true
    pkill -f "python.*main_novaic.py watchdog" 2>/dev/null || true
    pkill -f "python.*main_novaic.py task-worker" 2>/dev/null || true
    pkill -f "python.*main_novaic.py saga-worker" 2>/dev/null || true
    pkill -f "python.*main_novaic.py health" 2>/dev/null || true
    log_info "All services stopped"
}

reset_runtime_data() {
    log_warn "Resetting runtime data (tq_tasks/tq_sagas/agent_runtimes/chat_messages)..."
    sqlite3 "$NOVAIC_DATA_DIR/queue.db" "
DELETE FROM tq_sagas;
DELETE FROM tq_tasks;
"
    sqlite3 "$NOVAIC_DATA_DIR/runtime_orchestrator.db" "
DELETE FROM agent_runtimes;
DELETE FROM chat_messages;
UPDATE subagents SET status = 'sleeping';
"
    log_info "Runtime data reset complete"
}

show_status() {
    echo "=== Running Services ==="
    local ro_count=$(pgrep -f "python.*main_novaic.py runtime-orchestrator" 2>/dev/null | wc -l | tr -d ' ')
    local gateway_count=$(pgrep -f "python.*main_novaic.py gateway" 2>/dev/null | wc -l | tr -d ' ')
    local mcp_count=$(pgrep -f "python.*main_novaic.py tools-server" 2>/dev/null | wc -l | tr -d ' ')
    local queue_count=$(pgrep -f "python.*main_novaic.py queue-service" 2>/dev/null | wc -l | tr -d ' ')
    local watchdog_count=$(pgrep -f "python.*main_novaic.py watchdog" 2>/dev/null | wc -l | tr -d ' ')
    local task_count=$(pgrep -f "python.*main_novaic.py task-worker" 2>/dev/null | wc -l | tr -d ' ')
    local saga_count=$(pgrep -f "python.*main_novaic.py saga-worker" 2>/dev/null | wc -l | tr -d ' ')
    local health_count=$(pgrep -f "python.*main_novaic.py health" 2>/dev/null | wc -l | tr -d ' ')
    
    echo "Runtime Orch.: $ro_count"
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
  runtime-orchestrator  Start Runtime Orchestrator only
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

Configuration source:
  novaic-backend/config/services.json
  - paths.data_dir
  - services.gateway.url
  - services.tools_server.url
  - services.queue_service.url
  - worker.num_workers
EOF
}

ensure_dirs

case "${1:-all}" in
    runtime-orchestrator|ro) start_runtime_orchestrator ;;
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
        start_runtime_orchestrator
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
