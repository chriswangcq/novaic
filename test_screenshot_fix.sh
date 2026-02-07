#!/bin/bash
# 测试 VM 截图 API 修复

echo "VM 截图 API 修复验证"
echo "============================================================"
echo ""

# 获取 VM ID
VM_ID=$(curl -s http://localhost:8080/api/vms 2>/dev/null | python3 -c "import json, sys; vms = json.load(sys.stdin); print(vms[0]['id'] if vms else '')" 2>/dev/null)

if [ -z "$VM_ID" ]; then
    echo "❌ 未找到运行中的 VM"
    exit 1
fi

echo "✓ 找到 VM: $VM_ID"
echo ""

# 测试 1: vmcontrol 直接 API
echo "============================================================"
echo "测试 1: vmcontrol 直接 API (http://localhost:8080)"
echo "============================================================"
curl -s -X POST "http://localhost:8080/api/vms/$VM_ID/screenshot" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('✓ 返回 JSON 格式')
    print(f\"  - Has 'data': {'data' in data}\")
    print(f\"  - Has 'format': {'format' in data}\")
    print(f\"  - Format: {data.get('format')}\")
    if 'data' in data:
        print(f\"  - Data length: {len(data.get('data', ''))}\")
    else:
        print('❌ 缺少 data 字段')
        print(f'  - 实际字段: {list(data.keys())}')
except Exception as e:
    print(f'❌ JSON 解析失败: {e}')
"
echo ""

# 测试 2: Gateway 代理 API
echo "============================================================"
echo "测试 2: Gateway 代理 API (http://localhost:19999/api/vmcontrol)"
echo "============================================================"
curl -s -X POST "http://localhost:19999/api/vmcontrol/vms/$VM_ID/screenshot" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('✓ 返回 JSON 格式')
    print(f\"  - Has 'content': {'content' in data}\")
    
    if 'content' in data and data['content']:
        content = data['content'][0]
        print(f\"  - Content type: {content.get('type')}\")
        print(f\"  - Has 'data': {'data' in content}\")
        print(f\"  - MimeType: {content.get('mimeType')}\")
        if 'data' in content:
            print(f\"  - Data length: {len(content.get('data', ''))}\")
    else:
        print('❌ 缺少 content 字段或为空')
        print(f'  - 实际字段: {list(data.keys())}')
except Exception as e:
    print(f'❌ JSON 解析失败: {e}')
"
echo ""

# 测试 3: 检查 vmuse_adapter 代码
echo "============================================================"
echo "测试 3: 检查 vmuse_adapter 代码修复"
echo "============================================================"
if grep -q 'image_data = result.get("data") or result.get("image_data"' novaic-backend/gateway/clients/vmuse_adapter.py; then
    echo "✓ vmuse_adapter._screenshot 已修复"
    echo "  - 兼容 'data' 和 'image_data' 字段"
else
    echo "❌ vmuse_adapter._screenshot 未修复"
fi
echo ""

echo "============================================================"
echo "测试完成"
echo "============================================================"
