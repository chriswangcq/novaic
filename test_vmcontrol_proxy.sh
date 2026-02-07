#!/bin/bash

# VmControl 代理测试脚本
# 用于验证 Gateway 的 vmcontrol 代理功能

set -e

GATEWAY_URL="http://127.0.0.1:19999"
VMCONTROL_URL="http://127.0.0.1:8080"

echo "🧪 VmControl 代理功能测试"
echo "=========================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=${4:-}
    
    echo -n "测试 $name ... "
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$url" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$url" 2>/dev/null || echo "000")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ 成功${NC} (HTTP $http_code)"
        if [ -n "$body" ] && [ ${#body} -lt 200 ]; then
            echo "   响应: $body"
        fi
        return 0
    elif [ "$http_code" = "404" ]; then
        echo -e "${YELLOW}⚠️  404 (端点不存在或 VM 不存在)${NC}"
        return 1
    elif [ "$http_code" = "000" ]; then
        echo -e "${RED}❌ 连接失败${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠️  HTTP $http_code${NC}"
        if [ -n "$body" ] && [ ${#body} -lt 200 ]; then
            echo "   响应: $body"
        fi
        return 1
    fi
}

# 1. 测试 Gateway 健康检查
echo "1️⃣  测试 Gateway 健康检查"
echo "----------------------------"
test_endpoint "Gateway /api/health" "$GATEWAY_URL/api/health"
echo ""

# 2. 测试 VmControl 直接连接（可选）
echo "2️⃣  测试 VmControl 直接连接"
echo "----------------------------"
if test_endpoint "VmControl /api/health" "$VMCONTROL_URL/api/health"; then
    VMCONTROL_RUNNING=true
    echo -e "${GREEN}✅ VmControl 服务运行正常${NC}"
else
    VMCONTROL_RUNNING=false
    echo -e "${RED}❌ VmControl 服务未运行${NC}"
    echo "   提示: 请先启动 vmcontrol 服务"
fi
echo ""

# 3. 测试 Gateway 的 VmControl 代理健康检查
echo "3️⃣  测试 Gateway VmControl 代理健康检查"
echo "----------------------------------------"
test_endpoint "代理 /api/vmcontrol/health" "$GATEWAY_URL/api/vmcontrol/health"
echo ""

# 只在 vmcontrol 运行时测试其他端点
if [ "$VMCONTROL_RUNNING" = true ]; then
    echo "4️⃣  测试 VM 管理端点"
    echo "----------------------------"
    
    # 测试 VM 列表
    test_endpoint "获取 VM 列表" "$GATEWAY_URL/api/vmcontrol/vms"
    
    # 获取第一个 VM ID（如果有）
    VM_LIST=$(curl -s "$GATEWAY_URL/api/vmcontrol/vms" 2>/dev/null || echo "[]")
    VM_ID=$(echo "$VM_LIST" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    
    if [ -n "$VM_ID" ]; then
        echo ""
        echo "找到 VM: $VM_ID"
        echo ""
        
        # 测试 VM 信息
        test_endpoint "获取 VM 信息" "$GATEWAY_URL/api/vmcontrol/vms/$VM_ID"
        
        # 测试截图（不实际下载）
        test_endpoint "VM 截图" "$GATEWAY_URL/api/vmcontrol/vms/$VM_ID/screenshot" "POST"
        
        # 测试按键发送
        test_endpoint "发送按键" "$GATEWAY_URL/api/vmcontrol/vms/$VM_ID/keys" "POST" '{"keys":"ret"}'
        
        # 测试鼠标移动
        test_endpoint "鼠标移动" "$GATEWAY_URL/api/vmcontrol/vms/$VM_ID/mouse/move" "POST" '{"x":100,"y":200}'
        
        # 测试鼠标点击
        test_endpoint "鼠标点击" "$GATEWAY_URL/api/vmcontrol/vms/$VM_ID/mouse/click" "POST" '{"button":"left"}'
    else
        echo -e "${YELLOW}⚠️  没有找到运行的 VM，跳过 VM 操作测试${NC}"
    fi
    echo ""
    
    # 5. WebSocket 测试提示
    echo "5️⃣  WebSocket 测试"
    echo "----------------------------"
    echo "WebSocket 端点需要使用专门的工具测试，例如："
    echo ""
    echo "  使用 wscat:"
    echo "    npm install -g wscat"
    if [ -n "$VM_ID" ]; then
        echo "    wscat -c ws://127.0.0.1:19999/api/vmcontrol/vms/$VM_ID/vnc"
    else
        echo "    wscat -c ws://127.0.0.1:19999/api/vmcontrol/vms/{vm_id}/vnc"
    fi
    echo ""
    echo "  使用 websocat:"
    echo "    brew install websocat"
    if [ -n "$VM_ID" ]; then
        echo "    websocat ws://127.0.0.1:19999/api/vmcontrol/vms/$VM_ID/vnc"
    else
        echo "    websocat ws://127.0.0.1:19999/api/vmcontrol/vms/{vm_id}/vnc"
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️  VmControl 服务未运行，跳过其他测试${NC}"
    echo ""
    echo "要完成所有测试，请："
    echo "1. 启动 vmcontrol 服务"
    echo "2. 重新运行此脚本"
fi

echo ""
echo "=========================="
echo "✅ 测试完成"
echo ""
echo "查看详细日志："
echo "  Gateway: ~/.novaic/logs/gateway-*.log"
echo "  VmControl: 查看 vmcontrol 服务输出"
echo ""
echo "API 文档："
echo "  http://127.0.0.1:19999/docs"
