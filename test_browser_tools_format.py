#!/usr/bin/env python3
"""
浏览器工具统一格式验证脚本

验证所有已迁移的浏览器工具是否符合新的统一返回格式。
"""

import sys
import json
from typing import Dict, Any, List


def validate_unified_format(result: Dict[str, Any], tool_name: str) -> tuple[bool, List[str]]:
    """
    验证返回结果是否符合统一格式
    
    Args:
        result: 工具返回结果
        tool_name: 工具名称
    
    Returns:
        (is_valid, errors) - 是否有效和错误列表
    """
    errors = []
    
    # 检查必需字段
    if "success" not in result:
        errors.append(f"❌ 缺少 'success' 字段")
    
    if "content" not in result:
        errors.append(f"❌ 缺少 'content' 字段")
    elif not isinstance(result["content"], list):
        errors.append(f"❌ 'content' 不是数组，类型为: {type(result['content'])}")
    else:
        # 验证 content 数组元素
        for i, item in enumerate(result["content"]):
            if not isinstance(item, dict):
                errors.append(f"❌ content[{i}] 不是对象")
                continue
            
            if "type" not in item:
                errors.append(f"❌ content[{i}] 缺少 'type' 字段")
            else:
                item_type = item["type"]
                if item_type == "text":
                    if "text" not in item:
                        errors.append(f"❌ content[{i}] type='text' 但缺少 'text' 字段")
                elif item_type == "image":
                    if "data" not in item:
                        errors.append(f"❌ content[{i}] type='image' 但缺少 'data' 字段")
                    if "mimeType" not in item:
                        errors.append(f"⚠️  content[{i}] type='image' 建议添加 'mimeType' 字段")
    
    # 检查错误格式
    if result.get("success") == False:
        if "error" not in result:
            errors.append(f"⚠️  success=false 但没有 'error' 字段")
        if result.get("content") != []:
            errors.append(f"⚠️  success=false 但 content 不是空数组")
    
    return len(errors) == 0, errors


def mock_browser_navigate_response():
    """模拟 browser_navigate 返回"""
    return {
        "success": True,
        "content": [
            {
                "type": "text",
                "text": json.dumps({"success": True, "url": "https://example.com", "status": "loaded"}, ensure_ascii=False)
            }
        ]
    }


def mock_browser_click_response():
    """模拟 browser_click 返回"""
    return {
        "success": True,
        "content": [
            {
                "type": "text",
                "text": json.dumps({"success": True, "selector": "#button", "clicked": True}, ensure_ascii=False)
            }
        ]
    }


def mock_browser_content_response():
    """模拟 browser_content 返回（混合内容）"""
    return {
        "success": True,
        "content": [
            {
                "type": "text",
                "text": "页面标题：Example Domain\n这是示例页面的内容..."
            },
            {
                "type": "image",
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAUA",
                "mimeType": "image/png",
                "metadata": {
                    "compressed": True,
                    "original_size": 102400,
                    "compressed_size": 51200
                }
            }
        ]
    }


def mock_browser_error_response():
    """模拟错误返回"""
    return {
        "success": False,
        "error": "HTTP 404: URL not found",
        "content": []
    }


def main():
    """主测试函数"""
    print("=" * 60)
    print("浏览器工具统一格式验证")
    print("=" * 60)
    print()
    
    tests = [
        ("browser_navigate", mock_browser_navigate_response()),
        ("browser_click", mock_browser_click_response()),
        ("browser_content (混合内容)", mock_browser_content_response()),
        ("错误响应", mock_browser_error_response()),
    ]
    
    all_passed = True
    
    for tool_name, response in tests:
        print(f"【测试】{tool_name}")
        print("=" * 60)
        
        is_valid, errors = validate_unified_format(response, tool_name)
        
        if is_valid:
            print(f"✅ 格式验证通过")
            
            # 打印详细信息
            print(f"\n=== 返回格式详情 ===")
            print(f"success: {response['success']}")
            print(f"content 元素数: {len(response['content'])}")
            
            for i, item in enumerate(response["content"]):
                print(f"\n  元素 {i}:")
                print(f"    type: {item['type']}")
                
                if item['type'] == 'text':
                    text_preview = item['text'][:100]
                    if len(item['text']) > 100:
                        text_preview += "..."
                    print(f"    text: {text_preview}")
                elif item['type'] == 'image':
                    print(f"    data: {item['data'][:50]}... ({len(item['data'])} 字符)")
                    print(f"    mimeType: {item.get('mimeType', 'N/A')}")
                    if 'metadata' in item:
                        print(f"    metadata: {item['metadata']}")
            
            if "error" in response:
                print(f"\nerror: {response['error']}")
        else:
            print(f"❌ 格式验证失败")
            for error in errors:
                print(f"  {error}")
            all_passed = False
        
        print()
    
    # 总结
    print("=" * 60)
    if all_passed:
        print("✅ 所有测试通过")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分测试失败")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
