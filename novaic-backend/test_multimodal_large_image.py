#!/usr/bin/env python3
"""
测试大图片处理流程
模拟用户报告的 "卡死" 问题
"""

import sys
import json
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from task_queue.utils import multimodal
from task_queue.utils.context import process_multimodal_messages


def create_large_image_result():
    """创建一个包含大图片的工具结果（模拟真实场景）"""
    # 创建一个 646KB 的 base64 字符串（类似真实截图）
    base64_data = "iVBORw0KGgo" + "A" * (646 * 1024)  # 646KB
    
    return {
        "result": {  # 外层 result 包装
            "content": [
                {
                    "text": "Screenshot captured successfully. (compressed from 668KB to 646KB)",
                    "type": "text"
                },
                {
                    "data": base64_data,
                    "metadata": {
                        "compressed": True,
                        "compressed_size": 662092,
                        "compression_info": "(compressed from 668KB to 646KB)",
                        "compression_ratio": "96.7%",
                        "height": 800,
                        "original_size": 684516,
                        "width": 1280
                    },
                    "mimeType": "image/png",
                    "type": "image"
                }
            ],
            "success": True
        }
    }


def test_has_images():
    """测试 has_images 检测"""
    print("\n=== 测试 1: has_images 检测 ===")
    start = time.time()
    
    result = create_large_image_result()
    inner_result = result["result"]
    
    has_img = multimodal.has_images(inner_result)
    
    elapsed = time.time() - start
    print(f"✓ has_images = {has_img}")
    print(f"  耗时: {elapsed:.3f}s")
    
    if elapsed > 1.0:
        print(f"  ⚠️ 警告: 检测耗时过长 ({elapsed:.3f}s)")
    
    return has_img


def test_extract_from_result():
    """测试提取文本和图片"""
    print("\n=== 测试 2: extract_from_result ===")
    start = time.time()
    
    result = create_large_image_result()
    inner_result = result["result"]
    
    text, images = multimodal.extract_from_result(inner_result)
    
    elapsed = time.time() - start
    print(f"✓ 提取文本: {len(text)} 字符")
    print(f"✓ 提取图片: {len(images)} 张")
    if images:
        print(f"  - 图片大小: {len(images[0]['data'])} 字符")
    print(f"  耗时: {elapsed:.3f}s")
    
    if elapsed > 1.0:
        print(f"  ⚠️ 警告: 提取耗时过长 ({elapsed:.3f}s)")
    
    return text, images


def test_result_to_text_only():
    """测试转换为纯文本（移除图片数据）"""
    print("\n=== 测试 3: result_to_text_only ===")
    start = time.time()
    
    result = create_large_image_result()
    inner_result = result["result"]
    
    text_only = multimodal.result_to_text_only(inner_result)
    
    elapsed = time.time() - start
    print(f"✓ 纯文本版本: {len(text_only)} 字符")
    print(f"  耗时: {elapsed:.3f}s")
    
    # 检查是否正确移除了图片数据
    try:
        parsed = json.loads(text_only)
        for item in parsed.get("content", []):
            if item.get("type") == "image":
                if "data" in item and len(item["data"]) > 100:
                    print(f"  ❌ 错误: 图片数据没有被移除！")
                    return False
                else:
                    print(f"  ✓ 图片数据已被占位符替换")
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析错误: {e}")
        return False
    
    if elapsed > 1.0:
        print(f"  ⚠️ 警告: 转换耗时过长 ({elapsed:.3f}s)")
    
    return True


def test_process_multimodal_messages():
    """测试完整的消息处理流程"""
    print("\n=== 测试 4: process_multimodal_messages ===")
    start = time.time()
    
    result = create_large_image_result()
    
    # 模拟 tool result 消息
    messages = [
        {"role": "user", "content": "请截图"},
        {"role": "assistant", "tool_calls": [{"id": "call_123", "function": {"name": "browser_screenshot"}}]},
        {
            "role": "tool",
            "tool_call_id": "call_123",
            "name": "browser_screenshot",
            "content": json.dumps(result)  # 工具返回
        }
    ]
    
    # 处理消息（提取图片）
    processed = process_multimodal_messages(messages, provider="openai")
    
    elapsed = time.time() - start
    print(f"✓ 原始消息数: {len(messages)}")
    print(f"✓ 处理后消息数: {len(processed)}")
    print(f"  耗时: {elapsed:.3f}s")
    
    # 检查结果
    has_user_image = any(
        msg.get("role") == "user" and 
        isinstance(msg.get("content"), list) and
        any(item.get("type") == "image_url" for item in msg.get("content", []))
        for msg in processed
    )
    
    if has_user_image:
        print(f"  ✓ 图片已提取为独立的 user message")
    else:
        print(f"  ❌ 错误: 图片没有被提取")
        return False
    
    # 检查 tool result 是否包含大图片数据
    for msg in processed:
        if msg.get("role") == "tool":
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 100000:
                print(f"  ❌ 错误: tool result 仍包含大量数据 ({len(content)} 字符)")
                print(f"  这会导致 LLM API 调用缓慢或超时！")
                return False
            else:
                print(f"  ✓ tool result 大小合理: {len(content)} 字符")
    
    if elapsed > 2.0:
        print(f"  ⚠️ 警告: 处理耗时过长 ({elapsed:.3f}s)")
        print(f"  可能导致用户感觉 '卡死'")
    
    return True


def test_json_serialization():
    """测试 JSON 序列化性能"""
    print("\n=== 测试 5: JSON 序列化性能 ===")
    
    result = create_large_image_result()
    
    # 测试序列化
    start = time.time()
    json_str = json.dumps(result)
    elapsed = time.time() - start
    
    print(f"✓ 序列化大小: {len(json_str)} 字符")
    print(f"  耗时: {elapsed:.3f}s")
    
    if elapsed > 0.5:
        print(f"  ⚠️ 警告: 序列化耗时过长")
    
    # 测试反序列化
    start = time.time()
    parsed = json.loads(json_str)
    elapsed = time.time() - start
    
    print(f"✓ 反序列化完成")
    print(f"  耗时: {elapsed:.3f}s")
    
    if elapsed > 0.5:
        print(f"  ⚠️ 警告: 反序列化耗时过长")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("大图片处理性能测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # 测试 1
        if not test_has_images():
            all_passed = False
        
        # 测试 2
        test_extract_from_result()
        
        # 测试 3
        if not test_result_to_text_only():
            all_passed = False
        
        # 测试 4
        if not test_process_multimodal_messages():
            all_passed = False
        
        # 测试 5
        test_json_serialization()
        
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
