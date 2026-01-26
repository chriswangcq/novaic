#!/bin/bash

# NovAIC VM - 查看状态

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$VM_DIR/.vm.pid"

# 端口配置
VNC_PORT="${NOVAIC_VNC_PORT:-5900}"
MCP_PORT="${NOVAIC_MCP_PORT:-8080}"
SSH_PORT="${NOVAIC_SSH_PORT:-2222}"

echo ""
echo "════════════════════════════════════════════"
echo "  NovAIC VM - 状态"
echo "════════════════════════════════════════════"
echo ""

# 检查 VM 进程
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "VM 状态: ✅ 运行中 (PID: $PID)"
    else
        echo "VM 状态: ❌ 已停止 (PID 文件过期)"
        rm -f "$PID_FILE"
    fi
else
    echo "VM 状态: ❌ 未运行"
fi

echo ""
echo "端口检查:"

# 检查 SSH
if nc -z localhost "$SSH_PORT" 2>/dev/null; then
    echo "  SSH ($SSH_PORT):     ✅ 可连接"
else
    echo "  SSH ($SSH_PORT):     ❌ 不可用"
fi

# 检查 VNC
if nc -z localhost "$VNC_PORT" 2>/dev/null; then
    echo "  VNC ($VNC_PORT):     ✅ 可连接"
else
    echo "  VNC ($VNC_PORT):     ❌ 不可用"
fi

# 检查 MCP Server
if curl -s "http://localhost:$MCP_PORT/health" 2>/dev/null | grep -q "healthy"; then
    echo "  MCP ($MCP_PORT):     ✅ 服务正常"
else
    echo "  MCP ($MCP_PORT):     ⚠️  未部署或未启动"
fi

echo ""
echo "连接方式:"
echo "  VNC: vnc://localhost:$VNC_PORT"
echo "  SSH: ssh -p $SSH_PORT ubuntu@localhost"
echo "  MCP: http://localhost:$MCP_PORT/sse"
echo ""
