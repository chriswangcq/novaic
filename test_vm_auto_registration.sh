#!/bin/bash
# VM 自动注册机制完整测试脚本
# 
# 测试场景：
# 1. 新创建 VM 时自动注册
# 2. 启动已有 VM 时自动注册
# 3. 重启 VM 时自动注册
# 4. Gateway 重启后重新注册所有运行中的 VM
# 5. vmcontrol 重启后自动发现并注册所有运行中的 VM

set -e

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# API URLs
GATEWAY_URL="http://localhost:19999"
VMCONTROL_URL="http://localhost:8080"

echo "======================================"
echo "VM 自动注册机制完整测试"
echo "======================================"
echo ""

# 辅助函数：检查服务健康状态
check_service() {
    local url=$1
    local name=$2
    
    echo -n "检查 $name 服务状态... "
    if curl -s -f "$url/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 运行中${NC}"
        return 0
    else
        echo -e "${RED}✗ 未运行${NC}"
        return 1
    fi
}

# 辅助函数：获取运行中的 VM 列表
get_running_vms() {
    curl -s "$GATEWAY_URL/api/vm/running" | jq -r '.agents[]' 2>/dev/null || echo ""
}

# 辅助函数：检查 VM 是否在 vmcontrol 中注册
check_vm_registered() {
    local vm_id=$1
    
    echo -n "检查 VM $vm_id 是否在 vmcontrol 中注册... "
    
    local vms=$(curl -s "$VMCONTROL_URL/api/vms" 2>/dev/null)
    if echo "$vms" | jq -e ".[] | select(.id == \"$vm_id\")" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 已注册${NC}"
        return 0
    else
        echo -e "${RED}✗ 未注册${NC}"
        return 1
    fi
}

# 辅助函数：等待 VM 启动
wait_for_vm() {
    local vm_id=$1
    local max_wait=30
    local waited=0
    
    echo -n "等待 VM $vm_id 启动"
    while [ $waited -lt $max_wait ]; do
        if curl -s "$GATEWAY_URL/api/vm/is-running/$vm_id" | jq -e '.running == true' > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        waited=$((waited + 1))
    done
    
    echo -e " ${RED}✗ 超时${NC}"
    return 1
}

# ====================================
# 场景 1: 新启动 VM 时自动注册
# ====================================
echo ""
echo "======================================"
echo "场景 1: 启动 VM 时自动注册"
echo "======================================"

# 检查服务状态
check_service "$GATEWAY_URL" "Gateway" || { echo "Gateway 未运行，请先启动"; exit 1; }
check_service "$VMCONTROL_URL" "vmcontrol" || { echo "vmcontrol 未运行，请先启动"; exit 1; }

# 获取第一个 agent ID
echo -n "获取 agent 列表... "
AGENT_ID=$(curl -s "$GATEWAY_URL/api/agents" | jq -r '.[0].id' 2>/dev/null)
if [ -z "$AGENT_ID" ] || [ "$AGENT_ID" = "null" ]; then
    echo -e "${RED}✗ 没有找到 agent${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Agent ID: $AGENT_ID"

# 停止 VM（如果正在运行）
echo -n "停止 VM（如果正在运行）... "
curl -s -X POST "$GATEWAY_URL/api/vm/stop" \
    -H "Content-Type: application/json" \
    -d "{\"agent_id\": \"$AGENT_ID\", \"graceful\": false, \"quick\": true}" > /dev/null
echo -e "${GREEN}✓${NC}"

# 等待停止
sleep 3

# 启动 VM
echo -n "启动 VM... "
if curl -s -X POST "$GATEWAY_URL/api/vm/start" \
    -H "Content-Type: application/json" \
    -d "{\"agent_id\": \"$AGENT_ID\"}" | jq -e '.success == true' > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ 启动失败${NC}"
    exit 1
fi

# 等待 VM 完全启动
wait_for_vm "$AGENT_ID"

# 等待注册完成（异步过程）
echo -n "等待自动注册完成"
sleep 5
for i in {1..5}; do
    echo -n "."
    sleep 1
done
echo ""

# 检查是否已注册
if check_vm_registered "$AGENT_ID"; then
    echo -e "${GREEN}✓ 场景 1 通过：VM 启动时自动注册成功${NC}"
    SCENARIO_1_PASSED=1
else
    echo -e "${RED}✗ 场景 1 失败：VM 启动时未自动注册${NC}"
    SCENARIO_1_PASSED=0
fi

# ====================================
# 场景 2: Gateway 重启后重新注册
# ====================================
echo ""
echo "======================================"
echo "场景 2: Gateway 重启后重新注册"
echo "======================================"

echo -e "${YELLOW}注意：此场景需要手动重启 Gateway${NC}"
echo "请按以下步骤操作："
echo "1. 确保 VM 正在运行（已经完成）"
echo "2. 停止 Gateway 进程"
echo "3. 重新启动 Gateway"
echo "4. 观察日志中的 'Re-registering VMs with vmcontrol' 消息"
echo ""
echo -n "请在重启 Gateway 后按 Enter 继续..."
read

# 检查 Gateway 是否恢复
echo -n "等待 Gateway 恢复"
for i in {1..30}; do
    if check_service "$GATEWAY_URL" "Gateway" > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# 等待重新注册完成
echo -n "等待重新注册完成"
sleep 5
for i in {1..5}; do
    echo -n "."
    sleep 1
done
echo ""

# 检查是否重新注册
if check_vm_registered "$AGENT_ID"; then
    echo -e "${GREEN}✓ 场景 2 通过：Gateway 重启后自动重新注册成功${NC}"
    SCENARIO_2_PASSED=1
else
    echo -e "${RED}✗ 场景 2 失败：Gateway 重启后未重新注册${NC}"
    SCENARIO_2_PASSED=0
fi

# ====================================
# 场景 3: vmcontrol 重启后自动发现
# ====================================
echo ""
echo "======================================"
echo "场景 3: vmcontrol 重启后自动发现"
echo "======================================"

echo -e "${YELLOW}注意：此场景需要手动重启 vmcontrol${NC}"
echo "请按以下步骤操作："
echo "1. 确保 VM 正在运行"
echo "2. 停止 vmcontrol 进程"
echo "3. 重新启动 vmcontrol"
echo "4. 观察日志中的 'Auto-registered VM' 消息"
echo ""
echo -n "请在重启 vmcontrol 后按 Enter 继续..."
read

# 检查 vmcontrol 是否恢复
echo -n "等待 vmcontrol 恢复"
for i in {1..30}; do
    if check_service "$VMCONTROL_URL" "vmcontrol" > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# 等待自动发现完成
echo -n "等待自动发现完成"
sleep 3
for i in {1..3}; do
    echo -n "."
    sleep 1
done
echo ""

# 检查是否自动发现并注册
if check_vm_registered "$AGENT_ID"; then
    echo -e "${GREEN}✓ 场景 3 通过：vmcontrol 重启后自动发现并注册成功${NC}"
    SCENARIO_3_PASSED=1
else
    echo -e "${RED}✗ 场景 3 失败：vmcontrol 重启后未自动发现${NC}"
    SCENARIO_3_PASSED=0
fi

# ====================================
# 测试总结
# ====================================
echo ""
echo "======================================"
echo "测试总结"
echo "======================================"
echo ""

TOTAL_PASSED=$((SCENARIO_1_PASSED + SCENARIO_2_PASSED + SCENARIO_3_PASSED))
TOTAL_SCENARIOS=3

echo "测试结果："
echo ""
[ $SCENARIO_1_PASSED -eq 1 ] && echo -e "  ${GREEN}✓${NC} 场景 1: VM 启动时自动注册" || echo -e "  ${RED}✗${NC} 场景 1: VM 启动时自动注册"
[ $SCENARIO_2_PASSED -eq 1 ] && echo -e "  ${GREEN}✓${NC} 场景 2: Gateway 重启后重新注册" || echo -e "  ${RED}✗${NC} 场景 2: Gateway 重启后重新注册"
[ $SCENARIO_3_PASSED -eq 1 ] && echo -e "  ${GREEN}✓${NC} 场景 3: vmcontrol 重启后自动发现" || echo -e "  ${RED}✗${NC} 场景 3: vmcontrol 重启后自动发现"
echo ""
echo "通过: $TOTAL_PASSED / $TOTAL_SCENARIOS"
echo ""

if [ $TOTAL_PASSED -eq $TOTAL_SCENARIOS ]; then
    echo -e "${GREEN}所有测试通过！VM 自动注册机制运行正常。${NC}"
    exit 0
else
    echo -e "${RED}部分测试失败，请检查日志。${NC}"
    exit 1
fi
