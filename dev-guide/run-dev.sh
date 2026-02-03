#!/bin/bash
# NovAIC 开发环境启动脚本 (v17)
# 
# 用法:
#   ./run-dev.sh              # 启动所有服务
#   ./run-dev.sh gateway      # 只启动 Gateway
#   ./run-dev.sh mcp-gateway  # 只启动 MCP Gateway
#   ./run-dev.sh launcher     # 只启动 Launcher Service
#   ./run-dev.sh collector    # 只启动 Collector Service
#   ./run-dev.sh async        # 只启动 Async Service
#   ./run-dev.sh health       # 只启动 Health Service
#   ./run-dev.sh services     # 启动所有 Services (不含 Gateway)
#   ./run-dev.sh stop         # 停止所有服务

set -e

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GATEWAY_DIR="$PROJECT_ROOT/novaic-gateway"

# 数据目录
export NOVAIC_DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/.novaic}"
mkdir -p "$NOVAIC_DATA_DIR"

# Gateway URL
GATEWAY_URL="http://127.0.0.1:19999"
MCP_GATEWAY_URL="http://127.0.0.1:19998"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 venv
check_venv() {
    if [ ! -d "$GATEWAY_DIR/venv" ]; then
        log_error "Virtual environment not found at $GATEWAY_DIR/venv"
        log_info "Run: cd $GATEWAY_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
}

# 激活 venv
activate_venv() {
    source "$GATEWAY_DIR/venv/bin/activate"
}

# 启动 Gateway
start_gateway() {
    log_info "Starting Gateway on port 19999..."
    cd "$GATEWAY_DIR"
    activate_venv
    python main.py &
    sleep 2
    
    # 健康检查
    if curl -s "$GATEWAY_URL/api/health" > /dev/null; then
        log_info "Gateway started successfully"
    else
        log_error "Gateway failed to start"
        exit 1
    fi
}

# 启动 MCP Gateway
start_mcp_gateway() {
    log_info "Starting MCP Gateway on port 19998..."
    cd "$GATEWAY_DIR"
    activate_venv
    export NOVAIC_GATEWAY_URL="$GATEWAY_URL"
    python mcp_main.py &
    sleep 2
    
    # 健康检查
    if curl -s "$MCP_GATEWAY_URL/api/health" > /dev/null; then
        log_info "MCP Gateway started successfully"
    else
        log_error "MCP Gateway failed to start"
        exit 1
    fi
}

# 启动 Launcher Service
start_launcher() {
    log_info "Starting Launcher Service..."
    cd "$GATEWAY_DIR"
    activate_venv
    python launcher_main.py --gateway-url "$GATEWAY_URL" &
    log_info "Launcher Service started"
}

# 启动 Collector Service
start_collector() {
    log_info "Starting Collector Service..."
    cd "$GATEWAY_DIR"
    activate_venv
    python collector_main.py --gateway-url "$GATEWAY_URL" &
    log_info "Collector Service started"
}

# 启动 Async Service
start_async() {
    log_info "Starting Async Service..."
    cd "$GATEWAY_DIR"
    activate_venv
    python executor_main.py --gateway-url "$GATEWAY_URL" &
    log_info "Executor Service started"
}

# 启动 Health Service
start_health() {
    log_info "Starting Health Service..."
    cd "$GATEWAY_DIR"
    activate_venv
    python health_main.py --gateway-url "$GATEWAY_URL" &
    log_info "Health Service started"
}

# 启动 Monitor Service
start_monitor() {
    log_info "Starting Monitor Service..."
    cd "$GATEWAY_DIR"
    activate_venv
    python monitor_main.py --gateway-url "$GATEWAY_URL" &
    log_info "Monitor Service started"
}

# 启动所有 Services (不含 Gateway)
start_services() {
    start_monitor
    sleep 1
    start_launcher
    sleep 1
    start_collector
    start_async
    start_health
}

# 启动所有
start_all() {
    check_venv
    
    log_info "Starting all services..."
    log_info "Data directory: $NOVAIC_DATA_DIR"
    
    start_gateway
    start_mcp_gateway
    sleep 1
    start_services
    
    echo ""
    log_info "All services started!"
    echo ""
    echo "Gateway:     $GATEWAY_URL"
    echo "MCP Gateway: $MCP_GATEWAY_URL"
    echo ""
    echo "Health check:"
    echo "  curl $GATEWAY_URL/api/health"
    echo "  curl $MCP_GATEWAY_URL/api/health"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # 等待
    wait
}

# 停止所有
stop_all() {
    log_info "Stopping all services..."
    
    # 杀掉相关进程
    pkill -f "python.*main.py" 2>/dev/null || true
    pkill -f "python.*monitor_main.py" 2>/dev/null || true
    pkill -f "python.*launcher_main.py" 2>/dev/null || true
    pkill -f "python.*collector_main.py" 2>/dev/null || true
    pkill -f "python.*executor_main.py" 2>/dev/null || true
    pkill -f "python.*health_main.py" 2>/dev/null || true
    pkill -f "python.*mcp_main.py" 2>/dev/null || true
    pkill -f "python.*executor_main.py" 2>/dev/null || true
    
    log_info "All services stopped"
}

# 显示帮助
show_help() {
    echo "NovAIC Development Environment (v19)"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  (none)        Start all services"
    echo "  gateway       Start Gateway only (port 19999)"
    echo "  mcp-gateway   Start MCP Gateway only (port 19998)"
    echo "  monitor       Start Monitor Service (message watcher)"
    echo "  launcher      Start Launcher Service"
    echo "  collector     Start Collector Service"
    echo "  async         Start Async (Executor) Service"
    echo "  health        Start Health Service"
    echo "  services      Start all Services (Monitor, Launcher, Collector, Async, Health)"
    echo "  stop          Stop all services"
    echo "  help          Show this help"
    echo ""
    echo "Environment:"
    echo "  NOVAIC_DATA_DIR  Data directory (default: ~/.novaic)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start everything"
    echo "  $0 gateway            # Start Gateway only"
    echo "  $0 services           # Start Services after Gateway is running"
    echo "  $0 stop               # Stop all"
}

# 主入口
case "${1:-all}" in
    gateway)
        check_venv
        start_gateway
        wait
        ;;
    mcp-gateway)
        check_venv
        start_mcp_gateway
        wait
        ;;
    monitor)
        check_venv
        activate_venv
        cd "$GATEWAY_DIR"
        python monitor_main.py --gateway-url "$GATEWAY_URL"
        ;;
    launcher)
        check_venv
        activate_venv
        cd "$GATEWAY_DIR"
        python launcher_main.py --gateway-url "$GATEWAY_URL"
        ;;
    collector)
        check_venv
        activate_venv
        cd "$GATEWAY_DIR"
        python collector_main.py --gateway-url "$GATEWAY_URL"
        ;;
    async)
        check_venv
        activate_venv
        cd "$GATEWAY_DIR"
        python executor_main.py --gateway-url "$GATEWAY_URL"
        ;;
    health)
        check_venv
        activate_venv
        cd "$GATEWAY_DIR"
        python health_main.py --gateway-url "$GATEWAY_URL"
        ;;
    services)
        check_venv
        start_services
        wait
        ;;
    stop)
        stop_all
        ;;
    help|--help|-h)
        show_help
        ;;
    all|"")
        start_all
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
