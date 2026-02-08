#!/bin/bash
# VMUSE 一键部署脚本
# 将 VMUSE 代码部署到运行中的 VM

set -e

# 配置
VM_IP="127.0.0.1"
VM_SSH_PORT="20000"
VM_USER="ubuntu"
VM_PASS="ubuntu"
VM_VMUSE_PORT="18080"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 VMUSE 部署脚本${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# 检查 sshpass
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}❌ sshpass 未安装${NC}"
    echo "   安装: brew install sshpass (macOS) 或 apt install sshpass (Linux)"
    exit 1
fi

# 检查 VMUSE 源码
VMUSE_SRC="novaic-mcp-vmuse"
if [ ! -d "$VMUSE_SRC" ]; then
    echo -e "${RED}❌ VMUSE 源码目录不存在: $VMUSE_SRC${NC}"
    exit 1
fi

# 步骤 1: 检查 VM 状态
echo -e "${YELLOW}━━━ 步骤 1/6: 检查 VM 状态 ━━━${NC}"
if sshpass -p "$VM_PASS" ssh -p $VM_SSH_PORT -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
   $VM_USER@$VM_IP 'echo "VM 连接成功"' 2>/dev/null; then
    echo -e "${GREEN}✅ VM SSH 连接正常${NC}"
else
    echo -e "${RED}❌ 无法连接到 VM (端口 $VM_SSH_PORT)${NC}"
    echo "   请确保 VM 正在运行"
    exit 1
fi

# 步骤 2: 打包代码
echo ""
echo -e "${YELLOW}━━━ 步骤 2/6: 打包 VMUSE 代码 ━━━${NC}"
cd "$VMUSE_SRC"
TAR_FILE="/tmp/novaic-mcp-vmuse-$(date +%Y%m%d%H%M%S).tar.gz"
tar -czf "$TAR_FILE" . --exclude='.git' --exclude='__pycache__' --exclude='*.pyc'
TAR_SIZE=$(du -h "$TAR_FILE" | cut -f1)
echo -e "${GREEN}✅ 打包完成: $TAR_FILE ($TAR_SIZE)${NC}"
cd - > /dev/null

# 步骤 3: 传输到 VM
echo ""
echo -e "${YELLOW}━━━ 步骤 3/6: 传输到 VM ━━━${NC}"
sshpass -p "$VM_PASS" scp -P $VM_SSH_PORT -o StrictHostKeyChecking=no \
  "$TAR_FILE" $VM_USER@$VM_IP:/tmp/vmuse.tar.gz
echo -e "${GREEN}✅ 传输完成${NC}"

# 步骤 4: 部署代码
echo ""
echo -e "${YELLOW}━━━ 步骤 4/6: 部署代码 ━━━${NC}"
sshpass -p "$VM_PASS" ssh -p $VM_SSH_PORT -o StrictHostKeyChecking=no $VM_USER@$VM_IP << 'EOSSH'
set -e
cd /opt/novaic

# 备份旧版本（如果存在）
if [ -d "novaic-mcp-vmuse" ]; then
    echo "   备份旧版本..."
    mv novaic-mcp-vmuse novaic-mcp-vmuse.bak.$(date +%Y%m%d%H%M%S) || true
fi

# 创建目录并解压
mkdir -p novaic-mcp-vmuse
cd novaic-mcp-vmuse
tar -xzf /tmp/vmuse.tar.gz
echo "   ✓ 代码解压完成"

# 安装依赖
echo "   安装 Python 依赖..."
/opt/novaic/venv/bin/pip install -e . --quiet

# 确保依赖都已安装
/opt/novaic/venv/bin/pip install aiohttp pydantic pydantic-settings python-dotenv Pillow --quiet || true

echo "   ✓ 依赖安装完成"

# 清理临时文件
rm -f /tmp/vmuse.tar.gz
EOSSH

echo -e "${GREEN}✅ 部署完成${NC}"

# 步骤 5: 重启服务
echo ""
echo -e "${YELLOW}━━━ 步骤 5/6: 重启服务 ━━━${NC}"

# 先停止服务
sshpass -p "$VM_PASS" ssh -p $VM_SSH_PORT -o StrictHostKeyChecking=no $VM_USER@$VM_IP \
  'sudo systemctl stop novaic-vmuse' 2>/dev/null || true

sleep 2

# 启动服务
sshpass -p "$VM_PASS" ssh -p $VM_SSH_PORT -o StrictHostKeyChecking=no $VM_USER@$VM_IP \
  'sudo systemctl start novaic-vmuse'

echo "   等待服务启动..."
sleep 3

# 检查服务状态
SERVICE_STATUS=$(sshpass -p "$VM_PASS" ssh -p $VM_SSH_PORT -o StrictHostKeyChecking=no $VM_USER@$VM_IP \
  'sudo systemctl is-active novaic-vmuse' 2>/dev/null || echo "unknown")

if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "${GREEN}✅ 服务运行正常${NC}"
else
    echo -e "${RED}❌ 服务状态: $SERVICE_STATUS${NC}"
    echo "   查看日志: ssh -p $VM_SSH_PORT ubuntu@$VM_IP 'sudo journalctl -u novaic-vmuse -n 20'"
fi

# 步骤 6: 验证部署
echo ""
echo -e "${YELLOW}━━━ 步骤 6/6: 验证部署 ━━━${NC}"

# 健康检查
if curl -s -m 5 "http://$VM_IP:$VM_VMUSE_PORT/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  健康检查失败（服务可能还在启动中）${NC}"
fi

# 测试工具
echo "   测试核心工具..."
TEST_RESULT=$(curl -s -m 5 -X POST "http://$VM_IP:$VM_VMUSE_PORT/api/desktop/screenshot" \
  -H "Content-Type: application/json" -d '{}' 2>/dev/null || echo "{}")

if echo "$TEST_RESULT" | grep -q '"success".*true'; then
    echo -e "${GREEN}✅ 工具测试通过${NC}"
else
    echo -e "${YELLOW}⚠️  工具测试未通过（可能需要等待浏览器初始化）${NC}"
fi

# 完成
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "📋 服务信息:"
echo "   SSH: ssh -p $VM_SSH_PORT $VM_USER@$VM_IP (密码: $VM_PASS)"
echo "   API: http://$VM_IP:$VM_VMUSE_PORT"
echo "   健康: http://$VM_IP:$VM_VMUSE_PORT/health"
echo ""
echo "🔧 管理命令:"
echo "   查看状态: ssh -p $VM_SSH_PORT $VM_USER@$VM_IP 'sudo systemctl status novaic-vmuse'"
echo "   查看日志: ssh -p $VM_SSH_PORT $VM_USER@$VM_IP 'sudo journalctl -u novaic-vmuse -n 50'"
echo "   重启服务: ssh -p $VM_SSH_PORT $VM_USER@$VM_IP 'sudo systemctl restart novaic-vmuse'"
echo ""
echo "🧪 测试工具:"
echo "   完整测试: python3 /tmp/test_all_32_tools.py"
echo ""

# 清理临时文件
rm -f "$TAR_FILE"
