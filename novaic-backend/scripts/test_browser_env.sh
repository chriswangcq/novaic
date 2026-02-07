#!/bin/bash
# 测试浏览器环境

echo "=== 环境变量 ==="
env | grep -E "DISPLAY|XAUTHORITY|HOME|USER|PLAYWRIGHT"

echo ""
echo "=== 用户信息 ==="
whoami
id

echo ""
echo "=== X Authority ==="
ls -lh "$XAUTHORITY" 2>&1

echo ""
echo "=== X Server 连接测试 ==="
xdpyinfo -display "$DISPLAY" 2>&1 | head -5

echo ""
echo "=== Python 和 Playwright ==="
/opt/novaic/venv/bin/python3 -c "import sys; print(f'Python: {sys.version}'); from playwright.async_api import async_playwright; print('Playwright: OK')" 2>&1

echo ""
echo "=== Playwright 浏览器 ==="
ls -ld "$PLAYWRIGHT_BROWSERS_PATH" 2>&1
ls "$PLAYWRIGHT_BROWSERS_PATH/chromium-"* 2>&1 | head -3

echo ""
echo "=== 测试启动 Playwright ==="
/opt/novaic/venv/bin/python3 << 'PYEOF'
import asyncio
from playwright.async_api import async_playwright

async def test():
    try:
        print("[Test] Starting Playwright...")
        playwright = await async_playwright().start()
        print("[Test] ✓ Playwright started")
        
        print("[Test] Launching browser...")
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir="/home/ubuntu/.config/chromium",
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        print(f"[Test] ✓ Browser launched, pages: {len(context.pages)}")
        
        await context.close()
        await playwright.stop()
        print("[Test] ✓ Test complete")
    except Exception as e:
        print(f"[Test] ❌ Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
PYEOF
