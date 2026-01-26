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
echo "[1/3] 停止服务..."
$SSH_CMD "sudo systemctl stop novaic 2>/dev/null || true"

# Step 2: 复制代码
echo "[2/3] 复制代码..."
$SSH_CMD "rm -rf /opt/novaic-core/src"
$SCP_CMD -r "$NOVAIC_CORE_DIR/src" "$SSH_USER@$SSH_HOST:/opt/novaic-core/"

# Step 3: 重启服务
echo "[3/3] 重启服务..."
$SSH_CMD "sudo systemctl start novaic"

sleep 2

# 验证
MCP_PORT="${NOVAIC_MCP_PORT:-8080}"
if curl -s "http://localhost:$MCP_PORT/health" 2>/dev/null | grep -q "healthy"; then
    echo ""
    echo "✅ 快速部署完成!"
    echo ""
else
    echo ""
    echo "⚠️  服务启动中，稍等片刻..."
fi
