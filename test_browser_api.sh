#!/bin/bash
# 浏览器控制 API 测试脚本

set -e

VMCONTROL_URL="${VMCONTROL_URL:-http://localhost:9527}"
VM_ID="${VM_ID:-1}"

echo "========================================"
echo "浏览器控制 API 测试"
echo "========================================"
echo "vmcontrol URL: $VMCONTROL_URL"
echo "VM ID: $VM_ID"
echo ""

# 1. 测试导航到网页
echo "📍 测试 1: 导航到网页"
curl -X POST "$VMCONTROL_URL/api/vms/$VM_ID/browser/navigate" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  | jq '.'
echo ""

sleep 2

# 2. 测试获取页面内容
echo "📄 测试 2: 获取页面内容"
curl -X GET "$VMCONTROL_URL/api/vms/$VM_ID/browser/content" \
  | jq '.html' | head -20
echo ""

# 3. 测试截图
echo "📸 测试 3: 截图"
curl -X POST "$VMCONTROL_URL/api/vms/$VM_ID/browser/screenshot" \
  | jq -r '.data' | xxd -r -p > /tmp/browser_screenshot.png
echo "✅ 截图保存到 /tmp/browser_screenshot.png"
echo ""

# 4. 测试导航到 Google
echo "🔍 测试 4: 导航到 Google"
curl -X POST "$VMCONTROL_URL/api/vms/$VM_ID/browser/navigate" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}' \
  | jq '.'
echo ""

sleep 2

# 5. 测试输入文本
echo "⌨️  测试 5: 在搜索框输入文本"
curl -X POST "$VMCONTROL_URL/api/vms/$VM_ID/browser/type" \
  -H "Content-Type: application/json" \
  -d '{"selector": "textarea[name=q]", "text": "Playwright automation"}' \
  | jq '.'
echo ""

sleep 1

# 6. 测试点击
echo "🖱️  测试 6: 点击搜索按钮"
curl -X POST "$VMCONTROL_URL/api/vms/$VM_ID/browser/click" \
  -H "Content-Type: application/json" \
  -d '{"selector": "input[name=btnK]"}' \
  | jq '.'
echo ""

sleep 2

# 7. 最终截图
echo "📸 测试 7: 最终截图"
curl -X POST "$VMCONTROL_URL/api/vms/$VM_ID/browser/screenshot" \
  | jq -r '.data' | xxd -r -p > /tmp/browser_screenshot_final.png
echo "✅ 截图保存到 /tmp/browser_screenshot_final.png"
echo ""

echo "========================================"
echo "✅ 测试完成！"
echo "========================================"
echo ""
echo "查看截图："
echo "  open /tmp/browser_screenshot.png"
echo "  open /tmp/browser_screenshot_final.png"
