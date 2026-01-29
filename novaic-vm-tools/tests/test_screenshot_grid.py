#!/usr/bin/env python3
"""
测试截图坐标网格功能
"""

import asyncio
import base64

from novaic_vm_tools.tools import desktop


async def test_full_screenshot():
    """测试全屏截图（系统坐标从0开始）"""
    print("=" * 60)
    print("测试 1: 全屏截图（系统坐标 0,0 开始）")
    print("=" * 60)
    
    result = await desktop.DesktopTools.screenshot()
    
    if result.get("success"):
        print(f"✅ 截图成功")
        print(f"   尺寸: {result['width']}x{result['height']}")
        print(f"   Base64 长度: {len(result['screenshot'])} 字符")
        
        # 保存截图用于检查
        screenshot_bytes = base64.b64decode(result['screenshot'])
        with open("/tmp/test_full_screenshot.png", "wb") as f:
            f.write(screenshot_bytes)
        print(f"   已保存到: /tmp/test_full_screenshot.png")
        print(f"   请检查图片，坐标应该从 0 开始显示")
    else:
        print(f"❌ 截图失败: {result.get('error')}")


async def test_region_screenshot():
    """测试区域截图（系统坐标有偏移）"""
    print("\n" + "=" * 60)
    print("测试 2: 区域截图（系统坐标 500,300 开始）")
    print("=" * 60)
    
    # 截图系统坐标 (500, 300) 到 (1000, 800) 的区域
    region = {
        "x": 500,
        "y": 300,
        "width": 500,
        "height": 500
    }
    
    result = await desktop.DesktopTools.screenshot(region=region)
    
    if result.get("success"):
        print(f"✅ 截图成功")
        print(f"   截图区域: 系统坐标 ({region['x']}, {region['y']}) 到 ({region['x'] + region['width']}, {region['y'] + region['height']})")
        print(f"   尺寸: {result['width']}x{result['height']}")
        print(f"   Base64 长度: {len(result['screenshot'])} 字符")
        
        # 保存截图用于检查
        screenshot_bytes = base64.b64decode(result['screenshot'])
        with open("/tmp/test_region_screenshot.png", "wb") as f:
            f.write(screenshot_bytes)
        print(f"   已保存到: /tmp/test_region_screenshot.png")
        print(f"   请检查图片，坐标应该从 500, 300 开始显示（系统坐标）")
        print(f"   而不是从 0, 0 开始（像素坐标）")
    else:
        print(f"❌ 截图失败: {result.get('error')}")


async def main():
    """运行所有测试"""
    print("开始测试截图坐标网格功能...\n")
    
    try:
        # 测试全屏截图
        await test_full_screenshot()
        
        # 测试区域截图
        await test_region_screenshot()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        print("\n请检查生成的截图文件：")
        print("  - /tmp/test_full_screenshot.png (全屏，坐标从0开始)")
        print("  - /tmp/test_region_screenshot.png (区域，坐标从500,300开始)")
        print("\n验证要点：")
        print("  1. 截图上有红色网格线")
        print("  2. 顶部显示 X 坐标")
        print("  3. 左侧显示 Y 坐标")
        print("  4. 区域截图的坐标应该是系统坐标（500, 300...），不是像素坐标（0, 0...）")
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
