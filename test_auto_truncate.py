#!/usr/bin/env python3
"""
自动截断机制测试
测试 tools_server/executor.py 中的截断功能
"""

import sys
import os
import asyncio
import json

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "novaic-backend"))

from tools_server.executor import ToolExecutor


async def test_small_text_no_truncate():
    """测试 1: 小文本（< 4KB）不截断"""
    print("\n=== 测试 1: 小文本不截断 ===")
    
    executor = ToolExecutor(
        runtime_id="test-rt",
        agent_id="test-agent",
        subagent_id="test-subagent"
    )
    
    # 创建 1KB 文本
    result = {
        "success": True,
        "content": [
            {"type": "text", "text": "A" * 1000}
        ]
    }
    
    processed = await executor._handle_long_result(result, "test_tool")
    
    # 验证
    assert processed["content"][0]["text"] == "A" * 1000
    assert "_truncated" not in str(processed["content"])
    print("✅ 通过: 小文本未被截断")


async def test_medium_text_head_tail():
    """测试 2: 中等文本（4-10KB）head_tail 策略"""
    print("\n=== 测试 2: 中等文本 head_tail 策略 ===")
    
    executor = ToolExecutor(
        runtime_id="test-rt",
        agent_id="test-agent",
        subagent_id="test-subagent"
    )
    
    # 创建 5KB 文本
    result = {
        "success": True,
        "content": [
            {"type": "text", "text": "A" * 5000}
        ]
    }
    
    processed = await executor._handle_long_result(result, "test_tool")
    
    # 验证
    assert len(processed["content"]) >= 3, f"Expected >= 3 items, got {len(processed['content'])}"
    
    # 检查是否有省略标记
    has_marker = any("... [middle text content removed] ..." in item.get("text", "") 
                     for item in processed["content"])
    assert has_marker, "Missing truncation marker"
    
    # 检查截断元数据
    has_truncation = any(item.get("_truncated") for item in processed["content"])
    assert has_truncation, "Missing _truncated flag"
    
    # 检查 task_id
    assert "task_id" in processed, "Missing task_id"
    
    print("✅ 通过: 中等文本使用 head_tail 策略")


async def test_large_text_reference_only():
    """测试 3: 大文本（> 10KB）reference_only 策略"""
    print("\n=== 测试 3: 大文本 reference_only 策略 ===")
    
    executor = ToolExecutor(
        runtime_id="test-rt",
        agent_id="test-agent",
        subagent_id="test-subagent"
    )
    
    # 创建 15KB 文本
    result = {
        "success": True,
        "content": [
            {"type": "text", "text": "A" * 15000}
        ]
    }
    
    processed = await executor._handle_long_result(result, "test_tool")
    
    # 验证
    assert processed["content"][0].get("_truncated") == True
    assert processed["content"][0]["_truncation"]["strategy"] == "reference_only"
    assert "task_id" in processed
    
    # 检查原文本不在结果中
    original_in_result = any("A" * 1000 in item.get("text", "") 
                             for item in processed["content"])
    assert not original_in_result, "Original text should not be in result"
    
    print("✅ 通过: 大文本使用 reference_only 策略")


async def test_mixed_content_image_preserved():
    """测试 4: 图文混合（图像完整保留）"""
    print("\n=== 测试 4: 图文混合 - 图像不截断 ===")
    
    executor = ToolExecutor(
        runtime_id="test-rt",
        agent_id="test-agent",
        subagent_id="test-subagent"
    )
    
    # 创建图文混合内容（10KB 文本 + 图像）
    image_data = "base64_encoded_image_data_here" * 100  # 模拟图像数据
    result = {
        "success": True,
        "content": [
            {"type": "text", "text": "A" * 10000},
            {"type": "image", "data": image_data, "mimeType": "image/png"}
        ]
    }
    
    processed = await executor._handle_long_result(result, "screenshot_tool")
    
    # 验证图像完整
    image_items = [item for item in processed["content"] if item.get("type") == "image"]
    assert len(image_items) == 1, "Image should be preserved"
    assert image_items[0]["data"] == image_data, "Image data should not be truncated"
    assert "_truncated" not in image_items[0], "Image should not have _truncated flag"
    
    # 验证文本被截断
    text_items = [item for item in processed["content"] if item.get("type") == "text"]
    has_marker = any("... [middle text content removed] ..." in item.get("text", "") 
                     for item in text_items)
    assert has_marker, "Text should be truncated"
    
    print("✅ 通过: 图像完整保留，文本被截断")


async def test_calculate_size_ignores_images():
    """测试 5: 计算大小时忽略图像"""
    print("\n=== 测试 5: 计算大小忽略图像 ===")
    
    executor = ToolExecutor(
        runtime_id="test-rt",
        agent_id="test-agent",
        subagent_id="test-subagent"
    )
    
    # 创建图文混合内容
    content = [
        {"type": "text", "text": "A" * 1000},  # 1KB
        {"type": "image", "data": "B" * 1000000, "mimeType": "image/png"},  # 1MB (should be ignored)
        {"type": "text", "text": "C" * 1000},  # 1KB
    ]
    
    size = executor._calculate_content_size(content)
    
    # 验证：只计算文本大小 (2KB)，忽略图像 (1MB)
    assert size == 2000, f"Expected 2000 bytes, got {size}"
    
    print("✅ 通过: 计算大小时正确忽略图像")


async def test_utf8_boundary_safe():
    """测试 6: UTF-8 边界安全处理"""
    print("\n=== 测试 6: UTF-8 边界安全 ===")
    
    executor = ToolExecutor(
        runtime_id="test-rt",
        agent_id="test-agent",
        subagent_id="test-subagent"
    )
    
    # 创建包含多字节字符的文本
    result = {
        "success": True,
        "content": [
            {"type": "text", "text": "测试中文字符" * 500}  # 中文字符，每个 3 字节
        ]
    }
    
    processed = await executor._handle_long_result(result, "test_tool")
    
    # 验证：截断后的文本应该可以正确编码/解码
    for item in processed["content"]:
        if item.get("type") == "text":
            text = item["text"]
            try:
                # 尝试编码和解码
                encoded = text.encode("utf-8")
                decoded = encoded.decode("utf-8")
                assert decoded == text, "UTF-8 encoding/decoding failed"
            except UnicodeDecodeError:
                assert False, f"Invalid UTF-8 in truncated text: {text[:100]}"
    
    print("✅ 通过: UTF-8 边界安全处理")


async def test_empty_content():
    """测试 7: 空 content 数组"""
    print("\n=== 测试 7: 空 content 数组 ===")
    
    executor = ToolExecutor(
        runtime_id="test-rt",
        agent_id="test-agent",
        subagent_id="test-subagent"
    )
    
    # 空 content
    result = {
        "success": True,
        "content": []
    }
    
    processed = await executor._handle_long_result(result, "test_tool")
    
    # 验证：应原样返回
    assert processed["content"] == []
    assert "_truncated" not in str(processed)
    
    print("✅ 通过: 空 content 正确处理")


async def test_no_content_field():
    """测试 8: 没有 content 字段"""
    print("\n=== 测试 8: 没有 content 字段 ===")
    
    executor = ToolExecutor(
        runtime_id="test-rt",
        agent_id="test-agent",
        subagent_id="test-subagent"
    )
    
    # 没有 content 字段（传统格式）
    result = {
        "success": True,
        "result": "some data"
    }
    
    processed = await executor._handle_long_result(result, "test_tool")
    
    # 验证：应原样返回
    assert processed == result
    
    print("✅ 通过: 没有 content 字段正确处理")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("自动截断机制测试")
    print("=" * 60)
    
    tests = [
        test_small_text_no_truncate,
        test_medium_text_head_tail,
        test_large_text_reference_only,
        test_mixed_content_image_preserved,
        test_calculate_size_ignores_images,
        test_utf8_boundary_safe,
        test_empty_content,
        test_no_content_field,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            print(f"❌ 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 错误: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
