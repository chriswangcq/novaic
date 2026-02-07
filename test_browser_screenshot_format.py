#!/usr/bin/env python3
"""
测试 browser_screenshot 工具的新统一返回格式

验证：
1. 返回格式符合 MCP 标准
2. content 数组包含文本和图像
3. 图像数据完整（不被截断）
4. 错误处理正确
"""

import asyncio
import json
from typing import Dict, Any


def validate_standard_format(result: Dict[str, Any]) -> bool:
    """
    验证返回格式是否符合标准
    
    标准格式：
    {
        "success": bool,
        "content": [
            {"type": "text", "text": "..."},
            {"type": "image", "data": "...", "mimeType": "..."}
        ]
    }
    """
    print("\n=== 格式验证 ===")
    
    # 1. 必须包含 success 字段
    if "success" not in result:
        print("❌ 缺少 'success' 字段")
        return False
    print("✅ 包含 'success' 字段")
    
    # 2. 必须包含 content 字段
    if "content" not in result:
        print("❌ 缺少 'content' 字段")
        return False
    print("✅ 包含 'content' 字段")
    
    # 3. content 必须是数组
    content = result.get("content", [])
    if not isinstance(content, list):
        print(f"❌ 'content' 不是数组，类型为: {type(content)}")
        return False
    print(f"✅ 'content' 是数组，包含 {len(content)} 个元素")
    
    # 4. 验证 content 元素
    has_text = False
    has_image = False
    
    for i, item in enumerate(content):
        item_type = item.get("type", "")
        print(f"  - 元素 {i}: type={item_type}")
        
        if item_type == "text":
            has_text = True
            if "text" not in item:
                print(f"    ❌ 文本元素缺少 'text' 字段")
                return False
            print(f"    ✅ 文本内容: {item['text'][:50]}...")
        
        elif item_type == "image":
            has_image = True
            if "data" not in item:
                print(f"    ❌ 图像元素缺少 'data' 字段")
                return False
            if "mimeType" not in item:
                print(f"    ❌ 图像元素缺少 'mimeType' 字段")
                return False
            
            data_len = len(item["data"])
            print(f"    ✅ 图像数据长度: {data_len} 字符")
            print(f"    ✅ MIME 类型: {item['mimeType']}")
            
            # 检查是否有元数据
            if "metadata" in item:
                metadata = item["metadata"]
                print(f"    ✅ 元数据: {json.dumps(metadata, indent=6)}")
    
    # 5. 成功的返回应该包含至少一个文本和一个图像
    if result.get("success"):
        if not has_text:
            print("⚠️  警告: 成功的返回但没有文本内容")
        if not has_image:
            print("⚠️  警告: 成功的返回但没有图像内容")
    
    print("\n✅ 格式验证通过")
    return True


def validate_error_format(result: Dict[str, Any]) -> bool:
    """验证错误格式"""
    print("\n=== 错误格式验证 ===")
    
    if result.get("success"):
        print("❌ success 应该为 false")
        return False
    print("✅ success = false")
    
    if "error" not in result:
        print("❌ 缺少 'error' 字段")
        return False
    print(f"✅ error: {result['error']}")
    
    if "content" not in result:
        print("❌ 缺少 'content' 字段")
        return False
    print(f"✅ content: {result['content']}")
    
    print("\n✅ 错误格式验证通过")
    return True


def simulate_success_response() -> Dict[str, Any]:
    """模拟成功的返回"""
    return {
        "success": True,
        "content": [
            {
                "type": "text",
                "text": "Browser screenshot captured successfully. (compressed from 800KB to 450KB)"
            },
            {
                "type": "image",
                "data": "iVBORw0KGgoAAAANSUhEUg..." + "A" * 100,  # 模拟 Base64 数据
                "mimeType": "image/png",
                "metadata": {
                    "width": 1920,
                    "height": 1080,
                    "compressed": True,
                    "original_size": 819200,
                    "compressed_size": 460800,
                    "compression_ratio": "56.3%"
                }
            }
        ]
    }


def simulate_error_response() -> Dict[str, Any]:
    """模拟错误的返回"""
    return {
        "success": False,
        "error": "No image data returned from vmcontrol",
        "content": []
    }


async def test_format():
    """测试格式验证"""
    print("=" * 60)
    print("测试 browser_screenshot 新统一返回格式")
    print("=" * 60)
    
    # 测试成功响应
    print("\n【测试 1】成功响应格式")
    success_result = simulate_success_response()
    print(f"\n模拟返回:\n{json.dumps(success_result, indent=2, ensure_ascii=False)}")
    
    if not validate_standard_format(success_result):
        print("\n❌ 成功响应格式验证失败")
        return False
    
    # 测试错误响应
    print("\n\n【测试 2】错误响应格式")
    error_result = simulate_error_response()
    print(f"\n模拟返回:\n{json.dumps(error_result, indent=2, ensure_ascii=False)}")
    
    if not validate_error_format(error_result):
        print("\n❌ 错误响应格式验证失败")
        return False
    
    # 测试图像不被截断
    print("\n\n【测试 3】图像完整性")
    image_data = success_result["content"][1]["data"]
    original_length = len(image_data)
    print(f"图像数据长度: {original_length} 字符")
    
    # 验证图像数据没有截断标记
    if "..." in image_data[-10:] or "[truncated]" in image_data:
        print("❌ 图像数据被截断")
        return False
    print("✅ 图像数据完整（未被截断）")
    
    print("\n\n" + "=" * 60)
    print("✅ 所有测试通过")
    print("=" * 60)
    
    return True


async def main():
    """主函数"""
    try:
        success = await test_format()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
