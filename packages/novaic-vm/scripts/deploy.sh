#!/bin/bash

# NovAIC VM - 部署 novaic-core (MCP Server) 到虚拟机

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$VM_DIR")"

# novaic-core 源码位置
NOVAIC_CORE_DIR="${NOVAIC_CORE_DIR:-$PROJECT_ROOT/novaic-core}"

# SSH 配置
SSH_PORT="${NOVAIC_SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-ubuntu}"
SSH_HOST="${SSH_HOST:-127.0.0.1}"

SSH_CMD="ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p $SSH_PORT $SSH_USER@$SSH_HOST"
SCP_CMD="scp -o StrictHostKeyChecking=no -P $SSH_PORT"

echo ""
echo "════════════════════════════════════════════"
echo "  NovAIC VM - 部署 MCP Server"
echo "════════════════════════════════════════════"
echo ""
echo "源码: $NOVAIC_CORE_DIR"
echo "目标: $SSH_USER@$SSH_HOST:$SSH_PORT"
echo ""

# 检查源目录
if [ ! -d "$NOVAIC_CORE_DIR" ]; then
    echo "❌ 错误: novaic-core 目录不存在"
    echo "路径: $NOVAIC_CORE_DIR"
    echo ""
    echo "请设置 NOVAIC_CORE_DIR 环境变量，或确保目录结构正确"
    exit 1
fi

if [ ! -f "$NOVAIC_CORE_DIR/pyproject.toml" ]; then
    echo "❌ 错误: 无效的 novaic-core 目录 (缺少 pyproject.toml)"
    exit 1
fi

# ============================================================
# Step 1: 检查 VM 连接
# ============================================================
echo "[1/5] 检查 VM 连接..."

if ! $SSH_CMD "echo 'connected'" 2>/dev/null; then
    echo "❌ 错误: 无法连接到 VM"
    echo ""
    echo "请确保:"
    echo "  1. VM 已启动: ./scripts/start-vm.sh"
    echo "  2. cloud-init 已完成配置"
    echo ""
    echo "手动测试: ssh -p $SSH_PORT $SSH_USER@$SSH_HOST"
    exit 1
fi
echo "  ✓ VM 连接成功"

# ============================================================
# Step 2: 创建目录
# ============================================================
echo ""
echo "[2/5] 创建目录..."

$SSH_CMD "sudo mkdir -p /opt/novaic-core && sudo chown $SSH_USER:$SSH_USER /opt/novaic-core"
echo "  ✓ 目录已创建"

# ============================================================
# Step 3: 停止现有服务
# ============================================================
echo ""
echo "[3/5] 停止现有服务..."

$SSH_CMD "sudo systemctl stop novaic 2>/dev/null || pkill -f 'novaic_core' 2>/dev/null || true"
sleep 1
echo "  ✓ 已停止旧服务"

# ============================================================
# Step 4: 复制代码
# ============================================================
echo ""
echo "[4/5] 复制代码..."

# 清理旧代码
$SSH_CMD "rm -rf /opt/novaic-core/src /opt/novaic-core/pyproject.toml"

# 复制新代码
$SCP_CMD -r "$NOVAIC_CORE_DIR/src" "$SSH_USER@$SSH_HOST:/opt/novaic-core/"
$SCP_CMD "$NOVAIC_CORE_DIR/pyproject.toml" "$SSH_USER@$SSH_HOST:/opt/novaic-core/"
$SCP_CMD "$NOVAIC_CORE_DIR/README.md" "$SSH_USER@$SSH_HOST:/opt/novaic-core/" 2>/dev/null || true

echo "  ✓ 代码已复制"

# ============================================================
# Step 5: 安装依赖并启动服务
# ============================================================
echo ""
echo "[5/5] 安装依赖并启动服务..."

$SSH_CMD << 'INSTALL_SCRIPT'
set -e

echo "  检查 python3-venv..."
if ! dpkg -s python3-venv &> /dev/null; then
    echo "  安装 python3-venv..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3-venv
fi

echo "  创建虚拟环境..."
if [ ! -f /opt/novaic-venv/bin/activate ]; then
    sudo rm -rf /opt/novaic-venv
    sudo mkdir -p /opt/novaic-venv
    sudo chown $USER:$USER /opt/novaic-venv
    python3 -m venv /opt/novaic-venv
fi

source /opt/novaic-venv/bin/activate

echo "  安装依赖..."
pip install --upgrade pip -q
cd /opt/novaic-core
pip install -e . -q

# 安装 Playwright
echo "  配置 Playwright..."
if ! playwright --version &> /dev/null 2>&1; then
    pip install playwright -q
    playwright install chromium
    sudo playwright install-deps chromium 2>/dev/null || true
fi

echo "  ✓ 依赖安装完成"

# 启动服务
echo "  启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable novaic.service
sudo systemctl restart novaic.service

sleep 3

if systemctl is-active --quiet novaic.service; then
    echo "  ✓ novaic 服务已启动"
else
    echo "  ⚠️ 服务启动中..."
fi
INSTALL_SCRIPT

echo ""

# ============================================================
# 验证
# ============================================================
echo "验证服务..."
sleep 2

MCP_PORT="${NOVAIC_MCP_PORT:-8081}"

if curl -s "http://localhost:$MCP_PORT/health" 2>/dev/null | grep -q "healthy"; then
    echo ""
    echo "════════════════════════════════════════════"
    echo "  ✅ 部署成功!"
    echo "════════════════════════════════════════════"
    echo ""
    echo "MCP Server:"
    echo "  端点: http://localhost:$MCP_PORT/sse"
    echo "  文档: http://localhost:$MCP_PORT/docs"
    echo ""
    echo "Cursor 配置 (.cursor/mcp.json):"
    echo '  {'
    echo '    "mcpServers": {'
    echo '      "novaic": {'
    echo "        \"url\": \"http://localhost:$MCP_PORT/sse\""
    echo '      }'
    echo '    }'
    echo '  }'
else
    echo ""
    echo "⚠️  服务可能还在启动中"
    echo ""
    echo "检查命令:"
    echo "  ssh -p $SSH_PORT $SSH_USER@$SSH_HOST 'systemctl status novaic'"
    echo "  ssh -p $SSH_PORT $SSH_USER@$SSH_HOST 'journalctl -u novaic -f'"
fi

echo ""
