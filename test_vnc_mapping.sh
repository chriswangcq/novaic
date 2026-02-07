#!/bin/bash
# VM ID 映射测试脚本

set -e

echo "=== VM ID 映射测试 ==="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 检查 socket 文件
echo "1. 检查 VNC socket 文件..."
if ls /tmp/novaic/novaic-vnc-*.sock 2>/dev/null; then
    echo -e "${GREEN}✅ 找到 VNC socket 文件${NC}"
else
    echo -e "${YELLOW}⚠️  没有找到 VNC socket 文件（VM 可能未运行）${NC}"
fi
echo ""

# 2. 测试 vmcontrol 健康检查
echo "2. 测试 vmcontrol 健康检查..."
if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ vmcontrol 服务运行中${NC}"
    curl -s http://localhost:8080/health | jq '.' 2>/dev/null || curl -s http://localhost:8080/health
else
    echo -e "${RED}❌ vmcontrol 服务未运行${NC}"
    echo "   请先启动 vmcontrol:"
    echo "   cd novaic-app/src-tauri/vmcontrol && cargo run --release"
    exit 1
fi
echo ""

# 3. 测试 Gateway API
echo "3. 测试 Gateway API..."
if curl -sf http://localhost:10000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Gateway 服务运行中${NC}"
else
    echo -e "${RED}❌ Gateway 服务未运行${NC}"
    exit 1
fi
echo ""

# 4. 获取 VM 状态
echo "4. 获取 VM 状态（包含 agent_index）..."
STATUS=$(curl -s http://localhost:10000/api/vm/status 2>/dev/null || echo "{}")

if [ "$STATUS" = "{}" ] || [ "$STATUS" = "null" ]; then
    echo -e "${YELLOW}⚠️  没有运行中的 VM${NC}"
    echo "   请先启动 VM:"
    echo "   curl -X POST http://localhost:10000/api/vm/start -H 'Content-Type: application/json' -d '{\"agent_id\":\"test-1\",\"agent_index\":1,\"memory\":\"4096\",\"cpus\":4}'"
    exit 1
fi

echo "$STATUS" | jq '.' 2>/dev/null || echo "$STATUS"
echo ""

# 提取第一个 agent 的信息
AGENT_ID=$(echo "$STATUS" | jq -r 'keys[0]' 2>/dev/null)
AGENT_INDEX=$(echo "$STATUS" | jq -r ".\"$AGENT_ID\".agent_index" 2>/dev/null)

echo -e "${GREEN}Agent ID:${NC} $AGENT_ID"
echo -e "${GREEN}Agent Index:${NC} $AGENT_INDEX"
echo ""

# 5. 测试 VNC 端点（仅测试 HTTP 升级前的状态）
echo "5. 测试 VNC WebSocket 端点..."

# 测试 agent_index 格式
if [ "$AGENT_INDEX" != "null" ] && [ -n "$AGENT_INDEX" ]; then
    echo "   测试使用 agent_index: $AGENT_INDEX"
    
    # 尝试 HTTP GET（WebSocket 会返回 426 Upgrade Required，这是正常的）
    RESPONSE=$(curl -s -w "\n%{http_code}" "http://localhost:8080/api/vms/$AGENT_INDEX/vnc" 2>&1 || true)
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    
    if [ "$HTTP_CODE" = "426" ]; then
        echo -e "   ${GREEN}✅ agent_index 端点可访问（需要 WebSocket 升级）${NC}"
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "   ${RED}❌ Socket 文件未找到${NC}"
    else
        echo -e "   ${YELLOW}⚠️  HTTP $HTTP_CODE${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠️  agent_index 不可用${NC}"
fi
echo ""

# 测试 agent_id 格式
if [ "$AGENT_ID" != "null" ] && [ -n "$AGENT_ID" ]; then
    echo "   测试使用 agent_id (UUID): ${AGENT_ID:0:8}..."
    
    RESPONSE=$(curl -s -w "\n%{http_code}" "http://localhost:8080/api/vms/$AGENT_ID/vnc" 2>&1 || true)
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    
    if [ "$HTTP_CODE" = "426" ]; then
        echo -e "   ${GREEN}✅ agent_id 端点可访问（需要 WebSocket 升级）${NC}"
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "   ${RED}❌ Socket 文件未找到${NC}"
    else
        echo -e "   ${YELLOW}⚠️  HTTP $HTTP_CODE${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠️  agent_id 不可用${NC}"
fi
echo ""

# 6. 测试无效的 VM ID
echo "6. 测试错误处理..."
echo "   测试不存在的 agent_index..."
RESPONSE=$(curl -s "http://localhost:8080/api/vms/999/vnc" 2>&1 || true)
if echo "$RESPONSE" | grep -q "not found"; then
    echo -e "   ${GREEN}✅ 正确返回 404 错误${NC}"
else
    echo -e "   ${YELLOW}⚠️  未返回预期的错误${NC}"
fi
echo ""

echo "=== 测试总结 ==="
echo ""
echo "修复验证项："
echo "  • VNC socket 命名: novaic-vnc-{agent_index}.sock"
echo "  • Gateway 返回 agent_index: $AGENT_INDEX"
echo "  • vmcontrol 支持数字 ID: /api/vms/1/vnc"
echo "  • vmcontrol 支持 UUID: /api/vms/{uuid}/vnc"
echo ""
echo -e "${GREEN}✅ 基础功能测试完成${NC}"
echo ""
echo "下一步："
echo "  1. 在浏览器中测试 VNC 连接"
echo "  2. 检查前端日志是否使用 agent_index"
echo "  3. 验证多 VM 场景（如果需要）"
echo ""
