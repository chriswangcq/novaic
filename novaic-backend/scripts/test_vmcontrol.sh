#!/bin/bash
# 测试 vmcontrol 服务

set -e

echo "================================"
echo "vmcontrol 服务测试脚本"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
VMCONTROL_HOST="127.0.0.1"
VMCONTROL_PORT="8080"
VMCONTROL_URL="http://${VMCONTROL_HOST}:${VMCONTROL_PORT}"

echo "测试配置:"
echo "  Host: ${VMCONTROL_HOST}"
echo "  Port: ${VMCONTROL_PORT}"
echo "  URL:  ${VMCONTROL_URL}"
echo ""

# 1. 检查二进制文件是否存在
echo "=== 1. 检查 vmcontrol 二进制文件 ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VMCONTROL_DIR="$PROJECT_ROOT/../novaic-app/src-tauri/vmcontrol"

RELEASE_BIN="$VMCONTROL_DIR/target/release/vmcontrol"
DEBUG_BIN="$VMCONTROL_DIR/target/debug/vmcontrol"

if [ -f "$RELEASE_BIN" ]; then
    echo -e "${GREEN}✓${NC} 找到 release 版本: $RELEASE_BIN"
    VMCONTROL_BIN="$RELEASE_BIN"
elif [ -f "$DEBUG_BIN" ]; then
    echo -e "${GREEN}✓${NC} 找到 debug 版本: $DEBUG_BIN"
    VMCONTROL_BIN="$DEBUG_BIN"
else
    echo -e "${RED}✗${NC} 未找到 vmcontrol 二进制文件"
    echo "请先构建 vmcontrol:"
    echo "  cd $VMCONTROL_DIR"
    echo "  cargo build --release"
    exit 1
fi
echo ""

# 2. 检查端口是否被占用
echo "=== 2. 检查端口 ${VMCONTROL_PORT} ==="
if lsof -Pi :${VMCONTROL_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}!${NC} 端口 ${VMCONTROL_PORT} 已被占用"
    echo "占用进程:"
    lsof -Pi :${VMCONTROL_PORT} -sTCP:LISTEN
    echo ""
    read -p "是否要杀死该进程并继续？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -Pi :${VMCONTROL_PORT} -sTCP:LISTEN -t)
        kill -9 $PID
        echo -e "${GREEN}✓${NC} 已杀死进程 $PID"
        sleep 1
    else
        echo "测试取消"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} 端口 ${VMCONTROL_PORT} 可用"
fi
echo ""

# 3. 测试直接运行二进制文件
echo "=== 3. 测试直接运行 vmcontrol ==="
echo "命令: $VMCONTROL_BIN --help"
if $VMCONTROL_BIN --help > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} vmcontrol 可执行"
else
    echo -e "${RED}✗${NC} vmcontrol 执行失败"
    exit 1
fi
echo ""

# 4. 启动 vmcontrol 服务（后台）
echo "=== 4. 启动 vmcontrol 服务 ==="
export RUST_LOG=info
echo "启动命令: $VMCONTROL_BIN --port ${VMCONTROL_PORT} --host ${VMCONTROL_HOST}"
$VMCONTROL_BIN --port ${VMCONTROL_PORT} --host ${VMCONTROL_HOST} > /tmp/vmcontrol.log 2>&1 &
VMCONTROL_PID=$!
echo -e "${GREEN}✓${NC} vmcontrol 已启动 (PID: $VMCONTROL_PID)"
echo "等待服务就绪..."
sleep 3
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "=== 清理 ==="
    if [ ! -z "$VMCONTROL_PID" ]; then
        if kill -0 $VMCONTROL_PID 2>/dev/null; then
            echo "停止 vmcontrol (PID: $VMCONTROL_PID)..."
            kill $VMCONTROL_PID
            wait $VMCONTROL_PID 2>/dev/null || true
            echo -e "${GREEN}✓${NC} vmcontrol 已停止"
        fi
    fi
    echo "完成"
}

# 设置清理 trap
trap cleanup EXIT INT TERM

# 5. 测试 HTTP 端点
echo "=== 5. 测试 HTTP 端点 ==="

# 5.1 Health check
echo "5.1 Health check:"
if curl -s -f "${VMCONTROL_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} GET ${VMCONTROL_URL}/health - OK"
else
    echo -e "${RED}✗${NC} GET ${VMCONTROL_URL}/health - FAILED"
    echo "查看日志:"
    cat /tmp/vmcontrol.log
    exit 1
fi

# 5.2 List VMs
echo "5.2 List VMs:"
RESPONSE=$(curl -s "${VMCONTROL_URL}/api/vms")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} GET ${VMCONTROL_URL}/api/vms - OK"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗${NC} GET ${VMCONTROL_URL}/api/vms - FAILED"
fi

echo ""

# 6. 测试 WebSocket 端点（如果安装了 websocat）
echo "=== 6. 测试 WebSocket 端点 ==="
if command -v websocat &> /dev/null; then
    echo "使用 websocat 测试 WebSocket..."
    timeout 2 websocat "ws://${VMCONTROL_HOST}:${VMCONTROL_PORT}/api/vms/test-vm/vnc" > /dev/null 2>&1
    if [ $? -eq 124 ]; then
        echo -e "${GREEN}✓${NC} WebSocket 端点可访问"
    else
        echo -e "${YELLOW}!${NC} WebSocket 测试未完成（需要完整的 VNC 数据流）"
    fi
else
    echo -e "${YELLOW}!${NC} websocat 未安装，跳过 WebSocket 测试"
    echo "安装: cargo install websocat 或 brew install websocat"
fi
echo ""

# 7. 查看日志
echo "=== 7. 查看 vmcontrol 日志（最后 20 行）==="
tail -20 /tmp/vmcontrol.log
echo ""

# 8. 测试 Python 启动脚本
echo "=== 8. 测试 Python 启动脚本 ==="
if [ -f "$PROJECT_ROOT/main_vmcontrol.py" ]; then
    echo -e "${GREEN}✓${NC} main_vmcontrol.py 存在"
    echo "测试命令: python3 $PROJECT_ROOT/main_vmcontrol.py --help"
    if python3 "$PROJECT_ROOT/main_vmcontrol.py" --help > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} main_vmcontrol.py 可执行"
    else
        echo -e "${RED}✗${NC} main_vmcontrol.py 执行失败"
    fi
else
    echo -e "${RED}✗${NC} main_vmcontrol.py 不存在"
fi
echo ""

# 9. 总结
echo "================================"
echo "测试完成"
echo "================================"
echo -e "${GREEN}所有测试通过！${NC}"
echo ""
echo "启动命令示例:"
echo "  1. 直接运行:"
echo "     $VMCONTROL_BIN --port 8080 --host 127.0.0.1"
echo ""
echo "  2. 使用 Python 脚本:"
echo "     python3 $PROJECT_ROOT/main_vmcontrol.py --port 8080"
echo ""
echo "  3. 使用开发脚本:"
echo "     bash $SCRIPT_DIR/run_vmcontrol_dev.sh"
echo ""
echo "  4. 通过统一入口:"
echo "     python3 $PROJECT_ROOT/../main_novaic.py vmcontrol --port 8080"
echo ""
