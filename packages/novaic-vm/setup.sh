#!/bin/bash

# NovAIC VM - 一键安装脚本
# 自动检查依赖、创建并启动 QEMU 虚拟机

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}║   ${NC}NovAIC VM Setup${BLUE}                                        ║${NC}"
echo -e "${BLUE}║   ${NC}AI Computer - QEMU Linux VM with MCP Server${BLUE}            ║${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================
# Step 1: 检查系统要求
# ============================================================
echo -e "${YELLOW}[1/4]${NC} 检查系统要求..."

# 检查 macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${RED}❌ 错误: 目前只支持 macOS${NC}"
    exit 1
fi
echo "  ✓ macOS 检测通过"

# 检测架构
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    echo "  ✓ Apple Silicon (arm64)"
    QEMU_PACKAGE="qemu"
elif [ "$ARCH" = "x86_64" ]; then
    echo "  ✓ Intel (x86_64)"
    QEMU_PACKAGE="qemu"
else
    echo -e "${RED}❌ 错误: 不支持的架构: $ARCH${NC}"
    exit 1
fi

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ 错误: 需要 Homebrew${NC}"
    echo "  安装: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi
echo "  ✓ Homebrew 已安装"

# ============================================================
# Step 2: 安装依赖
# ============================================================
echo ""
echo -e "${YELLOW}[2/4]${NC} 检查/安装依赖..."

# 检查 QEMU
if ! command -v qemu-system-aarch64 &> /dev/null && ! command -v qemu-system-x86_64 &> /dev/null; then
    echo "  安装 QEMU..."
    brew install qemu
else
    echo "  ✓ QEMU 已安装"
fi

# 检查 cdrtools (用于创建 cloud-init ISO)
if ! command -v mkisofs &> /dev/null && ! command -v genisoimage &> /dev/null; then
    echo "  安装 cdrtools..."
    brew install cdrtools
else
    echo "  ✓ cdrtools 已安装"
fi

# ============================================================
# Step 3: 创建 VM
# ============================================================
echo ""
echo -e "${YELLOW}[3/4]${NC} 创建虚拟机..."

# 检查 VM 是否已存在
if [ -f "$SCRIPT_DIR/images/novaic-vm.qcow2" ]; then
    echo -e "${YELLOW}  VM 磁盘已存在。是否重新创建? (y/N)${NC}"
    read -r response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
        echo "  跳过创建，使用现有 VM"
    else
        bash "$SCRIPT_DIR/scripts/create-vm.sh"
    fi
else
    bash "$SCRIPT_DIR/scripts/create-vm.sh"
fi

# ============================================================
# Step 4: 启动 VM
# ============================================================
echo ""
echo -e "${YELLOW}[4/4]${NC} 启动虚拟机..."

bash "$SCRIPT_DIR/scripts/start-vm.sh"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║   ${NC}安装完成!${GREEN}                                              ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "首次启动需要 5-10 分钟完成系统配置..."
echo ""
echo "访问方式:"
echo "  VNC:  vnc://localhost:5900  (密码: novaic)"
echo "  SSH:  ssh -p 2222 ubuntu@localhost"
echo "  MCP:  http://localhost:8081/sse"
echo ""
echo "常用命令:"
echo "  启动 VM:  ./scripts/start-vm.sh"
echo "  停止 VM:  ./scripts/stop-vm.sh"
echo "  查看状态: ./scripts/status-vm.sh"
echo "  部署代码: ./scripts/deploy.sh"
echo ""
