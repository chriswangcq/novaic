#!/usr/bin/env bash
#
# NovAIC 开发环境启动脚本
#
# Usage:
#   ./run-dev.sh          # 启动全部四组件
#   ./run-dev.sh gateway  # 只启动 Gateway
#   ./run-dev.sh stop     # 停止所有组件
#   ./run-dev.sh status   # 查看状态
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
GATEWAY_DIR="$PROJECT_ROOT/novaic-gateway"
DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/Library/Application Support/com.novaic.app}"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查端口是否在监听
check_port() {
    local port=$1
    curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$port/" 2>/dev/null || echo "000"
}

# 停止所有组件
stop_all() {
    log_info "Stopping all components..."
    pkill -f "python main.py" 2>/dev/null || true
    pkill -f "python mcp_main.py" 2>/dev/null || true
    pkill -f "python master_main.py" 2>/dev/null || true
    pkill -f "python -m worker.worker" 2>/dev/null || true
    pkill -f "worker.worker" 2>/dev/null || true
    sleep 2
    log_info "All components stopped"
}

# 启动 Gateway
start_gateway() {
    log_info "Starting Gateway on port 19999..."
    cd "$GATEWAY_DIR"
    export NOVAIC_DATA_DIR="$DATA_DIR"
    nohup python main.py > /tmp/gateway.log 2>&1 &
    echo $! > /tmp/gateway.pid
    sleep 3
    
    if [ "$(check_port 19999)" = "200" ] || [ "$(check_port 19999)" = "404" ]; then
        log_info "Gateway started (PID: $(cat /tmp/gateway.pid))"
    else
        log_error "Gateway failed to start. Check /tmp/gateway.log"
        return 1
    fi
}

# 启动 MCP Gateway
start_mcp_gateway() {
    log_info "Starting MCP Gateway on port 19998..."
    cd "$GATEWAY_DIR"
    export NOVAIC_DATA_DIR="$DATA_DIR"
    export NOVAIC_GATEWAY_URL="http://127.0.0.1:19999"
    nohup python mcp_main.py > /tmp/mcp_gateway.log 2>&1 &
    echo $! > /tmp/mcp_gateway.pid
    sleep 3
    
    local status=$(check_port 19998)
    if [ "$status" = "200" ] || [ "$status" = "404" ]; then
        log_info "MCP Gateway started (PID: $(cat /tmp/mcp_gateway.pid))"
    else
        log_error "MCP Gateway failed to start (status: $status). Check /tmp/mcp_gateway.log"
        return 1
    fi
}

# 启动 Master
start_master() {
    log_info "Starting Master..."
    cd "$GATEWAY_DIR"
    export NOVAIC_DATA_DIR="$DATA_DIR"
    nohup python master_main.py \
        --gateway-url http://127.0.0.1:19999 \
        --mcp-gateway-url http://127.0.0.1:19998 \
        > /tmp/master.log 2>&1 &
    echo $! > /tmp/master.pid
    sleep 2
    log_info "Master started (PID: $(cat /tmp/master.pid))"
}

# 启动 Worker
start_worker() {
    log_info "Starting Worker..."
    cd "$GATEWAY_DIR"
    export NOVAIC_DATA_DIR="$DATA_DIR"
    nohup python -m worker.worker \
        --gateway http://127.0.0.1:19999 \
        --mcp-gateway-url http://127.0.0.1:19998 \
        > /tmp/worker.log 2>&1 &
    echo $! > /tmp/worker.pid
    sleep 2
    log_info "Worker started (PID: $(cat /tmp/worker.pid))"
}

# 显示状态
show_status() {
    echo ""
    echo "=== NovAIC Dev Environment Status ==="
    echo ""
    
    # Gateway - check /api/health specifically
    local gw_status=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:19999/api/health 2>/dev/null || echo "000")
    if [ "$gw_status" = "200" ]; then
        echo -e "Gateway (19999):     ${GREEN}● Running${NC}"
    else
        echo -e "Gateway (19999):     ${RED}○ Not running${NC} (status: $gw_status)"
    fi
    
    # MCP Gateway
    local mcp_status=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:19998/internal/mcp/stats 2>/dev/null || echo "000")
    if [ "$mcp_status" = "200" ]; then
        echo -e "MCP Gateway (19998): ${GREEN}● Running${NC}"
        # Show MCP stats
        local stats=$(curl -s http://127.0.0.1:19998/internal/mcp/stats 2>/dev/null)
        local agents=$(echo "$stats" | python -c "import sys,json; d=json.load(sys.stdin); print(d['stats']['total_agents_with_shared'])" 2>/dev/null || echo "?")
        local runtimes=$(echo "$stats" | python -c "import sys,json; d=json.load(sys.stdin); print(d['stats']['total_runtime_servers'])" 2>/dev/null || echo "?")
        echo "                     (agents: $agents, runtimes: $runtimes)"
    else
        echo -e "MCP Gateway (19998): ${RED}○ Not running${NC} (status: $mcp_status)"
    fi
    
    # Master
    if pgrep -f "python master_main.py" > /dev/null 2>&1; then
        echo -e "Master:              ${GREEN}● Running${NC}"
    else
        echo -e "Master:              ${RED}○ Not running${NC}"
    fi
    
    # Worker
    if pgrep -f "worker.worker" > /dev/null 2>&1; then
        echo -e "Worker:              ${GREEN}● Running${NC}"
    else
        echo -e "Worker:              ${RED}○ Not running${NC}"
    fi
    
    echo ""
    echo "=== Logs ==="
    echo "  Gateway:     /tmp/gateway.log"
    echo "  MCP Gateway: /tmp/mcp_gateway.log"
    echo "  Master:      /tmp/master.log"
    echo "  Worker:      /tmp/worker.log"
    echo ""
}

# 主逻辑
case "${1:-all}" in
    gateway)
        start_gateway
        ;;
    mcp-gateway|mcp)
        start_mcp_gateway
        ;;
    master)
        start_master
        ;;
    worker)
        start_worker
        ;;
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
    all|"")
        stop_all
        echo ""
        start_gateway
        start_mcp_gateway
        start_master
        start_worker
        echo ""
        show_status
        ;;
    *)
        echo "Usage: $0 [gateway|mcp-gateway|master|worker|stop|status|all]"
        exit 1
        ;;
esac
