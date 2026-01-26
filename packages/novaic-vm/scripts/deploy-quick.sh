#!/bin/bash

# NovAIC VM - 快速部署 (仅复制代码+重启服务，跳过依赖安装)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$VM_DIR")"

NOVAIC_CORE_DIR="${NOVAIC_CORE_DIR:-$PROJECT_ROOT/novaic-core}"

SSH_PORT="${NOVAIC_SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-ubuntu}"
SSH_HOST="${SSH_HOST:-127.0.0.1}"

SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=10"
SSH_CMD="ssh $SSH_OPTS -p $SSH_PORT $SSH_USER@$SSH_HOST"
SCP_CMD="scp $SSH_OPTS -P $SSH_PORT"

echo ""
echo "⚡ NovAIC VM - 快速部署 (代码更新)"
echo ""

# 检查源目录
if [ ! -d "$NOVAIC_CORE_DIR" ]; then
    echo "❌ 错误: novaic-core 目录不存在: $NOVAIC_CORE_DIR"
    exit 1
fi

# Step 1: 停止服务
echo "[1/4] 停止服务..."
$SSH_CMD "sudo systemctl stop novaic 2>/dev/null || true"

# Step 2: 复制代码
echo "[2/4] 复制代码..."
$SSH_CMD "rm -rf /opt/novaic-core/src /opt/novaic-core/skills"
$SCP_CMD -r "$NOVAIC_CORE_DIR/src" "$SSH_USER@$SSH_HOST:/opt/novaic-core/"
$SCP_CMD -r "$NOVAIC_CORE_DIR/skills" "$SSH_USER@$SSH_HOST:/opt/novaic-core/" 2>/dev/null || true

# Step 3: 确保服务文件是最新的 (FastMCP 版本)
echo "[3/4] 更新服务配置..."
$SSH_CMD 'sudo tee /etc/systemd/system/novaic.service > /dev/null' << 'SERVICE_EOF'
[Unit]
Description=NovAIC Core - MCP Server (FastMCP)
After=network.target display-manager.service x11vnc.service
Wants=display-manager.service

[Service]
Type=simple
User=ubuntu
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/ubuntu/.Xauthority
Environment=HOME=/home/ubuntu
Environment=PATH=/opt/novaic-venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/novaic-core/src
Environment=NOVAIC_HOST=0.0.0.0
Environment=NOVAIC_PORT=8080
WorkingDirectory=/opt/novaic-core
ExecStart=/opt/novaic-venv/bin/python -c "from novaic_core.main import mcp; mcp.run(transport='sse', host='0.0.0.0', port=8080)"
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Step 4: 重启服务
echo "[4/4] 重启服务..."
$SSH_CMD "sudo systemctl daemon-reload && sudo systemctl start novaic"

sleep 3

# 验证
MCP_PORT="${NOVAIC_MCP_PORT:-8080}"
echo ""
echo "验证服务..."

# 检查服务状态
if $SSH_CMD "systemctl is-active --quiet novaic.service"; then
    echo ""
    echo "✅ 快速部署完成!"
    echo ""
    echo "MCP Server: http://localhost:$MCP_PORT/sse"
else
    echo ""
    echo "⚠️  服务启动中，请检查日志:"
    echo "    ssh -p $SSH_PORT $SSH_USER@$SSH_HOST 'journalctl -u novaic -f'"
fi
