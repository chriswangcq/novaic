#!/bin/bash
#
# Phase 4.1 - VNC 配置验证脚本
# 快速检查 VNC 服务状态
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 输出函数
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 分隔线
separator() {
    echo "================================================================"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        error "Command not found: $1"
        return 1
    fi
    return 0
}

# 检查端口
check_port() {
    local port=$1
    local service=$2
    
    if nc -z localhost $port 2>/dev/null; then
        success "$service port $port is listening"
        return 0
    else
        error "$service port $port is NOT listening"
        return 1
    fi
}

# 主函数
main() {
    separator
    info "Phase 4.1 - VNC Configuration Verification"
    separator
    echo ""
    
    # 检查必要命令
    info "Checking required commands..."
    check_command "nc" || exit 1
    check_command "lsof" || exit 1
    check_command "ps" || exit 1
    success "All required commands available"
    echo ""
    
    # 读取 agent_index（默认为 1）
    AGENT_INDEX=${1:-1}
    info "Checking Agent $AGENT_INDEX..."
    echo ""
    
    # 计算端口
    BASE_PORT=$((20000 + AGENT_INDEX * 20))
    VNC_PORT=$((BASE_PORT + 6))
    WS_PORT=$((BASE_PORT + 7))
    SSH_PORT=$((BASE_PORT + 8))
    MCP_PORT=$((BASE_PORT + 0))
    
    info "Expected ports for Agent $AGENT_INDEX:"
    echo "  VNC:       $VNC_PORT"
    echo "  WebSocket: $WS_PORT"
    echo "  SSH:       $SSH_PORT"
    echo "  MCP:       $MCP_PORT"
    echo ""
    
    # 检查 QEMU 进程
    separator
    info "Checking QEMU process..."
    separator
    
    QEMU_PID=$(ps aux | grep "qemu-system" | grep "novaic-vm-$AGENT_INDEX" | grep -v grep | awk '{print $2}' | head -1)
    
    if [ -z "$QEMU_PID" ]; then
        error "QEMU process for Agent $AGENT_INDEX not found"
        info "Try starting the VM: POST /api/vm/start"
        exit 1
    else
        success "QEMU process found (PID: $QEMU_PID)"
        
        # 显示 QEMU 命令行（前 200 字符）
        QEMU_CMD=$(ps -p $QEMU_PID -o command= | cut -c1-200)
        info "QEMU command: $QEMU_CMD..."
    fi
    echo ""
    
    # 检查端口监听
    separator
    info "Checking port listeners..."
    separator
    
    FAILED=0
    
    check_port $VNC_PORT "VNC" || FAILED=$((FAILED + 1))
    check_port $WS_PORT "WebSocket" || FAILED=$((FAILED + 1))
    check_port $SSH_PORT "SSH" || FAILED=$((FAILED + 1))
    check_port $MCP_PORT "MCP" || FAILED=$((FAILED + 1))
    
    echo ""
    
    # 检查 Socket 文件
    separator
    info "Checking QEMU sockets..."
    separator
    
    SOCKET_DIR="/tmp/novaic"
    if [ ! -d "$SOCKET_DIR" ]; then
        # 尝试 macOS 临时目录
        SOCKET_DIR=$(find /var/folders -name "novaic" -type d 2>/dev/null | head -1)
    fi
    
    if [ -z "$SOCKET_DIR" ]; then
        warning "Socket directory not found"
    else
        info "Socket directory: $SOCKET_DIR"
        
        QMP_SOCK="$SOCKET_DIR/novaic-qmp-$AGENT_INDEX.sock"
        GA_SOCK="$SOCKET_DIR/novaic-ga-$AGENT_INDEX.sock"
        MCP_SOCK="$SOCKET_DIR/novaic-mcp-$AGENT_INDEX.sock"
        
        [ -S "$QMP_SOCK" ] && success "QMP socket: $QMP_SOCK" || error "QMP socket not found"
        [ -S "$GA_SOCK" ] && success "Guest Agent socket: $GA_SOCK" || error "Guest Agent socket not found"
        [ -S "$MCP_SOCK" ] && success "MCP socket: $MCP_SOCK" || error "MCP socket not found"
    fi
    
    echo ""
    
    # Gateway API 检查
    separator
    info "Checking Gateway API..."
    separator
    
    GATEWAY_URL="http://localhost:19999"
    
    if curl -s -f "$GATEWAY_URL/api/health" > /dev/null 2>&1; then
        success "Gateway is running at $GATEWAY_URL"
        
        # 获取 VNC 状态
        info "Fetching VNC status..."
        VNC_STATUS=$(curl -s "$GATEWAY_URL/api/vnc/status" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            echo "$VNC_STATUS" | python3 -m json.tool 2>/dev/null || echo "$VNC_STATUS"
        else
            warning "Failed to fetch VNC status from Gateway"
        fi
    else
        warning "Gateway is not responding at $GATEWAY_URL"
        info "Start Gateway: cd novaic-backend && python main.py"
    fi
    
    echo ""
    
    # 总结
    separator
    if [ $FAILED -eq 0 ]; then
        success "All checks passed! VNC is ready."
        info "Frontend URL: ws://localhost:$WS_PORT/websockify"
    else
        error "$FAILED check(s) failed"
        info "See PHASE_4_1_QUICK_REFERENCE.md for troubleshooting"
    fi
    separator
    
    echo ""
    info "For detailed documentation, see:"
    echo "  - PHASE_4_1_EXECUTIVE_SUMMARY.md"
    echo "  - PHASE_4_1_QUICK_REFERENCE.md"
    echo "  - PHASE_4_1_VNC_INVESTIGATION_REPORT.md"
}

# 运行主函数
main "$@"
