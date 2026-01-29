#!/bin/bash

# NovAIC VM - 部署 novaic-mcp-vmuse (MCP Server) 到虚拟机

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$VM_DIR")"

# novaic-mcp-vmuse 源码位置
NOVAIC_MCP_VMUSE_DIR="${NOVAIC_MCP_VMUSE_DIR:-$PROJECT_ROOT/novaic-mcp-vmuse}"

# SSH 配置
SSH_PORT="${NOVAIC_SSH_PORT:-20008}"
SSH_USER="${SSH_USER:-ubuntu}"
SSH_HOST="${SSH_HOST:-127.0.0.1}"

# SSH 选项：跳过 host key 检查（VM 重建后 key 会变）
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=10"
SSH_CMD="ssh $SSH_OPTS -p $SSH_PORT $SSH_USER@$SSH_HOST"
SCP_CMD="scp $SSH_OPTS -P $SSH_PORT"

echo ""
echo "════════════════════════════════════════════"
echo "  NovAIC VM - 部署 MCP Server"
echo "════════════════════════════════════════════"
echo ""
echo "源码: $NOVAIC_MCP_VMUSE_DIR"
echo "目标: $SSH_USER@$SSH_HOST:$SSH_PORT"
echo ""

# 检查源目录
if [ ! -d "$NOVAIC_MCP_VMUSE_DIR" ]; then
    echo "❌ 错误: novaic-mcp-vmuse 目录不存在"
    echo "路径: $NOVAIC_MCP_VMUSE_DIR"
    echo ""
    echo "请设置 NOVAIC_MCP_VMUSE_DIR 环境变量，或确保目录结构正确"
    exit 1
fi

if [ ! -f "$NOVAIC_MCP_VMUSE_DIR/pyproject.toml" ]; then
    echo "❌ 错误: 无效的 novaic-mcp-vmuse 目录 (缺少 pyproject.toml)"
    exit 1
fi

# ============================================================
# Step 1: 检查 VM 连接（失败后重试）
# ============================================================
echo "[1/6] 检查 VM 连接..."

max_retries=10
retry_interval=20
retry_count=0

while ! $SSH_CMD "echo 'connected'" 2>/dev/null; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
        echo "❌ 错误: 无法连接到 VM (已重试 $max_retries 次)"
        echo ""
        echo "请确保:"
        echo "  1. VM 已启动: ./scripts/start-vm.sh"
        echo "  2. cloud-init 已完成配置"
        echo ""
        echo "手动测试: ssh -p $SSH_PORT $SSH_USER@$SSH_HOST"
        exit 1
    fi
    echo "  连接失败，${retry_interval}秒后重试 ($retry_count/$max_retries)..."
    sleep $retry_interval
done
echo "  ✓ VM 连接成功"

# 等待 cloud-init 完成（实时显示日志）
echo ""
echo "[1.5/6] 等待 cloud-init 完成..."
echo ""
echo "════════════════════════════════════════════"
echo "  cloud-init 日志 (实时)"
echo "════════════════════════════════════════════"

# 后台启动 tail -f 显示 cloud-init 日志
$SSH_CMD "tail -f /var/log/cloud-init-output.log 2>/dev/null" &
TAIL_PID=$!

# 等待完成标记文件出现
while ! $SSH_CMD "test -f /var/log/novaic-init-done.log" 2>/dev/null; do
    sleep 5
done

# 停止 tail 进程
kill $TAIL_PID 2>/dev/null || true
wait $TAIL_PID 2>/dev/null || true

echo ""
echo "════════════════════════════════════════════"
echo "  ✓ cloud-init 已完成"
echo "════════════════════════════════════════════"

# ============================================================
# Step 2: 配置 pip 源
# ============================================================
echo ""
echo "[2/6] 配置 pip 源..."

# 根据 USE_CN_MIRRORS 环境变量决定 pip 源
USE_CN_MIRRORS="${USE_CN_MIRRORS:-0}"
if [ "$USE_CN_MIRRORS" = "1" ]; then
    PIP_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
    PIP_TRUSTED_HOST="mirrors.aliyun.com"
    echo "  ✓ 使用中国镜像源 (阿里云)"
else
    PIP_INDEX_URL="https://pypi.org/simple/"
    PIP_TRUSTED_HOST="pypi.org"
    echo "  ✓ 使用官方源"
fi

# ============================================================
# Step 3: 创建目录
# ============================================================
echo ""
echo "[3/6] 创建目录..."

$SSH_CMD "sudo mkdir -p /opt/novaic-mcp-vmuse && sudo chown $SSH_USER:$SSH_USER /opt/novaic-mcp-vmuse"
echo "  ✓ 目录已创建"

# ============================================================
# Step 4: 停止现有服务
# ============================================================
echo ""
echo "[4/6] 停止现有服务..."

$SSH_CMD "sudo systemctl stop novaic 2>/dev/null || pkill -f 'novaic_mcp_vmuse' 2>/dev/null || true"
sleep 1
echo "  ✓ 已停止旧服务"

# ============================================================
# Step 5: 复制代码
# ============================================================
echo ""
echo "[5/6] 复制代码..."

# 清理旧代码
$SSH_CMD "rm -rf /opt/novaic-mcp-vmuse/src /opt/novaic-mcp-vmuse/skills /opt/novaic-mcp-vmuse/pyproject.toml"

# 复制新代码
$SCP_CMD -r "$NOVAIC_MCP_VMUSE_DIR/src" "$SSH_USER@$SSH_HOST:/opt/novaic-mcp-vmuse/"
$SCP_CMD -r "$NOVAIC_MCP_VMUSE_DIR/skills" "$SSH_USER@$SSH_HOST:/opt/novaic-mcp-vmuse/" 2>/dev/null || true
$SCP_CMD "$NOVAIC_MCP_VMUSE_DIR/pyproject.toml" "$SSH_USER@$SSH_HOST:/opt/novaic-mcp-vmuse/"
$SCP_CMD "$NOVAIC_MCP_VMUSE_DIR/README.md" "$SSH_USER@$SSH_HOST:/opt/novaic-mcp-vmuse/" 2>/dev/null || true

echo "  ✓ 代码已复制"

# ============================================================
# Step 6: 安装依赖并启动服务
# ============================================================
echo ""
echo "[6/6] 安装依赖并启动服务..."

# 传递 pip 源配置到 VM
$SSH_CMD "PIP_INDEX_URL='$PIP_INDEX_URL' PIP_TRUSTED_HOST='$PIP_TRUSTED_HOST' bash -s" << 'INSTALL_SCRIPT'
set -e

# 检查 venv 是否存在（cloud-init 应该已经创建）
if [ ! -f /opt/novaic-venv/bin/activate ]; then
    echo "  创建 venv (cloud-init 可能失败了)..."
    
    # 等待 apt/dpkg 进程结束
    max_wait=300
    waited=0
    while pgrep -x "apt-get\|apt\|dpkg\|unattended-upgr" > /dev/null 2>&1; do
        if [ $waited -eq 0 ]; then
            echo "  等待 apt 进程结束..."
        fi
        sleep 5
        waited=$((waited + 5))
        if [ $waited -ge $max_wait ]; then
            echo "  ⚠️ 等待超时，继续尝试..."
            break
        fi
    done
    
    if ! dpkg -s python3-venv &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq python3-venv
    fi
    
    sudo rm -rf /opt/novaic-venv
    sudo mkdir -p /opt/novaic-venv
    sudo chown $USER:$USER /opt/novaic-venv
    python3 -m venv /opt/novaic-venv
else
    echo "  ✓ venv 已存在"
fi

source /opt/novaic-venv/bin/activate

# 检查 fastmcp 是否安装（作为依赖安装的指示器）
if ! python -c "import fastmcp" &> /dev/null 2>&1; then
    echo "  安装依赖 (cloud-init 可能失败了)..."
    pip install --upgrade pip -q -i "$PIP_INDEX_URL" --trusted-host "$PIP_TRUSTED_HOST"
    cd /opt/novaic-mcp-vmuse
    pip install -e . -q -i "$PIP_INDEX_URL" --trusted-host "$PIP_TRUSTED_HOST"
else
    echo "  ✓ 依赖已安装，跳过"
    # 仍然用 editable 模式链接代码
    cd /opt/novaic-mcp-vmuse
    pip install -e . -q --no-deps 2>/dev/null || true
fi

# 检查 Playwright chromium 是否安装
if [ ! -d ~/.cache/ms-playwright/chromium-* ]; then
    echo "  安装 Playwright chromium (cloud-init 可能失败了)..."
    pip install playwright -q -i "$PIP_INDEX_URL" --trusted-host "$PIP_TRUSTED_HOST" 2>/dev/null || true
    playwright install chromium
    sudo playwright install-deps chromium 2>/dev/null || true
else
    echo "  ✓ Playwright chromium 已安装，跳过"
fi

echo "  ✓ 依赖检查完成"

# 更新 systemd 服务文件 (FastMCP 版本 - Streamable HTTP)
# 绑定到 0.0.0.0 以便 QEMU 端口转发可以访问
# 安全性：VM 使用 user networking，没有外部网络接口
# 宿主机端口转发绑定到 127.0.0.1，外部无法访问
echo "  更新服务配置..."
sudo tee /etc/systemd/system/novaic.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=NovAIC VM Tools - MCP Server (FastMCP)
After=network.target display-manager.service x11vnc.service
Wants=display-manager.service

[Service]
Type=simple
User=ubuntu
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/ubuntu/.Xauthority
Environment=HOME=/home/ubuntu
Environment=PATH=/opt/novaic-venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/novaic-mcp-vmuse/src
WorkingDirectory=/opt/novaic-mcp-vmuse
ExecStart=/opt/novaic-venv/bin/python -c "from novaic_mcp_vmuse.main import mcp; mcp.run(transport='streamable-http', host='0.0.0.0', port=8080)"
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# 启动服务
echo "  启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable novaic.service
sudo systemctl stop novaic-virtio-proxy.service 2>/dev/null || true
sudo systemctl disable novaic-virtio-proxy.service 2>/dev/null || true
sudo systemctl restart novaic.service

sleep 3

if systemctl is-active --quiet novaic.service; then
    echo "  ✓ novaic 服务已启动"
else
    echo "  ⚠️ novaic 服务启动中..."
fi
INSTALL_SCRIPT

echo ""

# ============================================================
# 验证
# ============================================================
echo "验证服务..."
sleep 2

MCP_PORT="${NOVAIC_MCP_PORT:-8080}"

# 检查服务状态
if $SSH_CMD "systemctl is-active --quiet novaic.service"; then
    echo ""
    echo "════════════════════════════════════════════"
    echo "  ✅ 部署成功!"
    echo "════════════════════════════════════════════"
    echo ""
    echo "MCP Server (FastMCP - Streamable HTTP):"
    echo "  MCP 端点: http://localhost:$MCP_PORT/mcp"
    echo ""
    echo "Cursor 配置 (.cursor/mcp.json):"
    echo '  {'
    echo '    "mcpServers": {'
    echo '      "novaic": {'
    echo "        \"url\": \"http://localhost:$MCP_PORT/mcp\""
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
