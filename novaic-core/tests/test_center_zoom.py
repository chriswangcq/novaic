#!/usr/bin/env python3
"""
测试中心焦点和放大倍数截图功能
"""

import asyncio
import base64

from novaic_core.tools import desktop


async def test_center_zoom_screen_center():
    """测试使用屏幕中心，2倍放大"""
    print("\n" + "=" * 60)
    print("测试 1: 屏幕中心，2倍放大 (center=None, zoom_factor=2.0)")
    print("=" * 60)
    
    result = await desktop.DesktopTools.screenshot(
        center=None,
        zoom_factor=2.0,
        grid_density="normal"
    )
    
    if result.get("success"):
        print(f"✅ 截图成功")
        print(f"   尺寸: {result['width']}x{result['height']}")
        print(f"   Base64 长度: {len(result['screenshot'])} 字符")
        
        # 保存截图
        screenshot_bytes = base64.b64decode(result['screenshot'])
        with open("/tmp/test_center_zoom_screen_center_2x.png", "wb") as f:
            f.write(screenshot_bytes)
        print(f"   已保存到: /tmp/test_center_zoom_screen_center_2x.png")
    else:
        print(f"❌ 截图失败: {result.get('error')}")


async def test_center_zoom_minus_one():
    """测试使用(-1, -1)作为中心，4倍放大"""
    print("\n" + "=" * 60)
    print("测试 2: 屏幕中心，4倍放大 (center=(-1, -1), zoom_factor=4.0)")
    print("=" * 60)
    
    result = await desktop.DesktopTools.screenshot(
        center={"x": -1, "y": -1},
        zoom_factor=4.0,
        grid_density="fine"
    )
    
    if result.get("success"):
        print(f"✅ 截图成功")
        print(f"   尺寸: {result['width']}x{result['height']}")
        print(f"   Base64 长度: {len(result['screenshot'])} 字符")
        
        # 保存截图
        screenshot_bytes = base64.b64decode(result['screenshot'])
        with open("/tmp/test_center_zoom_minus_one_4x.png", "wb") as f:
            f.write(screenshot_bytes)
        print(f"   已保存到: /tmp/test_center_zoom_minus_one_4x.png")
    else:
        print(f"❌ 截图失败: {result.get('error')}")


async def test_center_zoom_specific_point():
    """测试指定中心点，2倍放大"""
    print("\n" + "=" * 60)
    print("测试 3: 指定中心点(960, 540)，2倍放大")
    print("=" * 60)
    
    result = await desktop.DesktopTools.screenshot(
        center={"x": 960, "y": 540},
        zoom_factor=2.0,
        grid_density="normal"
    )
    
    if result.get("success"):
        print(f"✅ 截图成功")
        print(f"   尺寸: {result['width']}x{result['height']}")
        print(f"   Base64 长度: {len(result['screenshot'])} 字符")
        
        # 保存截图
        screenshot_bytes = base64.b64decode(result['screenshot'])
        with open("/tmp/test_center_zoom_specific_2x.png", "wb") as f:
            f.write(screenshot_bytes)
        print(f"   已保存到: /tmp/test_center_zoom_specific_2x.png")
    else:
        print(f"❌ 截图失败: {result.get('error')}")


async def test_center_zoom_edge_case():
    """测试边缘情况：中心点靠近屏幕边缘，需要padding"""
    print("\n" + "=" * 60)
    print("测试 4: 边缘情况 - 中心点(100, 100)，2倍放大（需要padding）")
    print("=" * 60)
    
    result = await desktop.DesktopTools.screenshot(
        center={"x": 100, "y": 100},
        zoom_factor=2.0,
        grid_density="normal"
    )
    
    if result.get("success"):
        print(f"✅ 截图成功")
        print(f"   尺寸: {result['width']}x{result['height']}")
        print(f"   Base64 长度: {len(result['screenshot'])} 字符")
        
        # 保存截图
        screenshot_bytes = base64.b64decode(result['screenshot'])
        with open("/tmp/test_center_zoom_edge_2x.png", "wb") as f:
            f.write(screenshot_bytes)
        print(f"   已保存到: /tmp/test_center_zoom_edge_2x.png")
        print(f"   注意：此截图应该包含白色padding区域")
    else:
        print(f"❌ 截图失败: {result.get('error')}")


async def test_center_zoom_corner_case():
    """测试角落情况：中心点在屏幕角落"""
    print("\n" + "=" * 60)
    print("测试 5: 角落情况 - 中心点(50, 50)，4倍放大（需要大量padding）")
    print("=" * 60)
    
    result = await desktop.DesktopTools.screenshot(
        center={"x": 50, "y": 50},
        zoom_factor=4.0,
        grid_density="fine"
    )
    
    if result.get("success"):
        print(f"✅ 截图成功")
        print(f"   尺寸: {result['width']}x{result['height']}")
        print(f"   Base64 长度: {len(result['screenshot'])} 字符")
        
        # 保存截图
        screenshot_bytes = base64.b64decode(result['screenshot'])
        with open("/tmp/test_center_zoom_corner_4x.png", "wb") as f:
            f.write(screenshot_bytes)
        print(f"   已保存到: /tmp/test_center_zoom_corner_4x.png")
        print(f"   注意：此截图应该包含大量白色padding区域")
    else:
        print(f"❌ 截图失败: {result.get('error')}")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试中心焦点和放大倍数截图功能...")
    print("=" * 60)
    
    try:
        # 测试屏幕中心（center=None）
        await test_center_zoom_screen_center()
        
        # 测试屏幕中心（center=(-1, -1)）
        await test_center_zoom_minus_one()
        
        # 测试指定中心点
        await test_center_zoom_specific_point()
        
        # 测试边缘情况
        await test_center_zoom_edge_case()
        
        # 测试角落情况
        await test_center_zoom_corner_case()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        print("\n请检查生成的截图文件：")
        print("  - /tmp/test_center_zoom_screen_center_2x.png")
        print("  - /tmp/test_center_zoom_minus_one_4x.png")
        print("  - /tmp/test_center_zoom_specific_2x.png")
        print("  - /tmp/test_center_zoom_edge_2x.png (应该包含padding)")
        print("  - /tmp/test_center_zoom_corner_4x.png (应该包含大量padding)")
        print("\n验证要点：")
        print("  1. 所有截图都应该以指定的中心点为中心")
        print("  2. 放大倍数正确（2x显示更小区域，4x显示更小区域）")
        print("  3. 边缘和角落情况应该有白色padding填充")
        print("  4. 坐标网格应该正确显示系统坐标")
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
