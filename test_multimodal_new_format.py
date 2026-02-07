#!/usr/bin/env python3
"""
测试多模态处理对新格式的兼容性

验证 has_images() 和 extract_from_result() 对新格式的支持
"""

import json
import sys
import os

# 添加路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "novaic-backend"))

from task_queue.utils import multimodal
from task_queue.utils.context import process_multimodal_messages


def test_has_images_new_format_text_only():
    """测试：新格式（纯文本）"""
    print("\n[测试 1] 新格式（纯文本）")
    result = {
        "success": True,
        "content": [{"type": "text", "text": "Hello"}]
    }
    
    has_img = multimodal.has_images(result)
    print(f"  has_images: {has_img}")
    assert has_img == False, "纯文本不应该被检测为有图片"
    print("  ✅ 通过")


def test_has_images_new_format_with_image():
    """测试：新格式（含图片）"""
    print("\n[测试 2] 新格式（含图片）")
    result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Screenshot"},
            {"type": "image", "data": "iVBORw0KG" + "G" * 100, "mimeType": "image/png"}
        ]
    }
    
    has_img = multimodal.has_images(result)
    print(f"  has_images: {has_img}")
    assert has_img == True, "应该检测到新格式的图片"
    print("  ✅ 通过")


def test_has_images_new_format_multiple_images():
    """测试：新格式（多个图片）"""
    print("\n[测试 3] 新格式（多个图片）")
    result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Multiple images"},
            {"type": "image", "data": "iVBORw0KGgoAAAANS" + "A" * 100, "mimeType": "image/png"},
            {"type": "image", "data": "/9j/4AAQSkZJRgABA" + "Q" * 100, "mimeType": "image/jpeg"}
        ]
    }
    
    has_img = multimodal.has_images(result)
    print(f"  has_images: {has_img}")
    assert has_img == True, "应该检测到多个图片"
    print("  ✅ 通过")


def test_extract_from_result_new_format():
    """测试：extract_from_result() 对新格式的支持"""
    print("\n[测试 4] extract_from_result() 新格式")
    result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Screenshot captured"},
            {"type": "image", "data": "iVBORw0KG" + "G" * 100, "mimeType": "image/png"}
        ]
    }
    
    text, images = multimodal.extract_from_result(result)
    
    print(f"  text: {text}")
    print(f"  images count: {len(images)}")
    if images:
        print(f"  images[0] mime_type: {images[0].get('mime_type')}")
        print(f"  images[0] data length: {len(images[0].get('data', ''))}")
    
    assert text == "Screenshot captured", f"文本提取错误: {text}"
    assert len(images) == 1, f"应该提取到 1 个图片，实际: {len(images)}"
    assert images[0]["mime_type"] == "image/png", "MIME 类型错误"
    assert "iVBORw0KG" in images[0]["data"], "图片数据错误"
    print("  ✅ 通过")


def test_extract_from_result_multiple_images():
    """测试：提取多个图片"""
    print("\n[测试 5] extract_from_result() 多个图片")
    # 使用有效的 base64 字符
    result = {
        "content": [
            {"type": "text", "text": "Two screenshots"},
            {"type": "image", "data": "iVBORw0KGgoAAAANS" + "A" * 100, "mimeType": "image/png"},
            {"type": "text", "text": "Between images"},
            {"type": "image", "data": "/9j/4AAQSkZJRgABA" + "Q" * 100, "mimeType": "image/jpeg"}
        ]
    }
    
    text, images = multimodal.extract_from_result(result)
    
    print(f"  text: {text}")
    print(f"  images count: {len(images)}")
    
    assert "Two screenshots" in text, "文本提取错误"
    assert "Between images" in text, "文本提取错误"
    assert len(images) == 2, f"应该提取到 2 个图片，实际: {len(images)}"
    assert images[0]["mime_type"] == "image/png", "第一个图片 MIME 类型错误"
    assert images[1]["mime_type"] == "image/jpeg", "第二个图片 MIME 类型错误"
    print("  ✅ 通过")


def test_backward_compatibility_old_format():
    """测试：向后兼容旧格式"""
    print("\n[测试 6] 向后兼容（旧格式）")
    old_result = {
        "success": True,
        "screenshot": "iVBORw0KG" + "O" * 100,
        "message": "Done"
    }
    
    has_img = multimodal.has_images(old_result)
    text, images = multimodal.extract_from_result(old_result)
    
    print(f"  has_images: {has_img}")
    print(f"  images count: {len(images)}")
    
    assert has_img == True, "应该检测到旧格式的图片"
    assert len(images) == 1, "应该提取到 1 个图片"
    print("  ✅ 通过")


def test_result_to_text_only_new_format():
    """测试：result_to_text_only() 对新格式的清理"""
    print("\n[测试 7] result_to_text_only() 新格式")
    result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Screenshot"},
            {"type": "image", "data": "iVBORw0KG" + "G" * 1000, "mimeType": "image/png"}
        ]
    }
    
    text_only = multimodal.result_to_text_only(result)
    text_only_dict = json.loads(text_only)
    
    print(f"  cleaned content: {json.dumps(text_only_dict, indent=2)}")
    
    assert "content" in text_only_dict, "应该保留 content 字段"
    assert len(text_only_dict["content"]) == 2, "应该保留 2 个 item"
    assert text_only_dict["content"][0]["type"] == "text", "文本项应该保留"
    assert text_only_dict["content"][1]["type"] == "image", "图片项类型应该保留"
    assert text_only_dict["content"][1].get("_placeholder") == True, "图片应该被替换为占位符"
    assert "data" not in text_only_dict["content"][1], "图片数据应该被移除"
    print("  ✅ 通过")


def test_process_multimodal_messages_new_format():
    """测试：端到端处理（Context 处理）"""
    print("\n[测试 8] process_multimodal_messages() 新格式")
    tool_result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Screenshot captured"},
            {"type": "image", "data": "iVBORw0KG" + "G" * 100, "mimeType": "image/png"}
        ]
    }
    
    messages = [
        {"role": "tool", "tool_call_id": "call_1", "name": "screenshot", 
         "content": json.dumps(tool_result)}
    ]
    
    processed = process_multimodal_messages(messages, provider="openai")
    
    print(f"  原始消息数: {len(messages)}")
    print(f"  处理后消息数: {len(processed)}")
    
    # 应该生成 2 个消息：tool result (text only) + user (image)
    assert len(processed) == 2, f"应该生成 2 个消息，实际: {len(processed)}"
    assert processed[0]["role"] == "tool", "第一个消息应该是 tool result"
    assert processed[1]["role"] == "user", "第二个消息应该是 user（图片）"
    assert isinstance(processed[1]["content"], list), "图片消息的 content 应该是数组"
    
    # 检查 OpenAI 格式
    img_content = processed[1]["content"]
    assert len(img_content) == 2, "应该有 2 个 content 项（图片 + 描述）"
    assert img_content[0]["type"] == "image_url", "第一个项应该是 image_url"
    assert "url" in img_content[0]["image_url"], "应该有 url 字段"
    assert img_content[0]["image_url"]["url"].startswith("data:image/png;base64,"), "应该是 data URL"
    
    # 检查 tool result 已清理
    tool_content = json.loads(processed[0]["content"])
    assert tool_content["content"][1].get("_placeholder") == True, "图片应该被替换为占位符"
    
    print("  ✅ 通过")


def test_edge_cases():
    """测试：边界情况"""
    print("\n[测试 9] 边界情况")
    
    # 空 content 数组
    result1 = {"success": True, "content": []}
    assert multimodal.has_images(result1) == False, "空数组不应该有图片"
    print("  ✅ 空 content 数组")
    
    # content 不是数组
    result2 = {"success": True, "content": "some string"}
    assert multimodal.has_images(result2) == False, "非数组 content 不应该有图片"
    print("  ✅ content 不是数组")
    
    # 无效的图片项（缺少 data）
    result3 = {
        "content": [
            {"type": "image"}  # 缺少 data
        ]
    }
    assert multimodal.has_images(result3) == False, "缺少 data 的图片不应该被检测"
    print("  ✅ 无效图片项")
    
    # 无效的图片项（data 为空）
    result4 = {
        "content": [
            {"type": "image", "data": ""}  # data 为空
        ]
    }
    assert multimodal.has_images(result4) == False, "空 data 的图片不应该被检测"
    print("  ✅ 空 data")
    
    # 无效的图片项（data 太短）
    result5 = {
        "content": [
            {"type": "image", "data": "abc"}  # 太短
        ]
    }
    assert multimodal.has_images(result5) == False, "太短的 data 不应该被检测为图片"
    print("  ✅ data 太短")
    
    print("  ✅ 所有边界情况通过")


def test_mime_type_variants():
    """测试：MIME 类型变体"""
    print("\n[测试 10] MIME 类型变体")
    
    # 标准拼写：mimeType
    result1 = {
        "content": [
            {"type": "image", "data": "BASE64" + "X" * 100, "mimeType": "image/png"}
        ]
    }
    _, images1 = multimodal.extract_from_result(result1)
    assert images1[0]["mime_type"] == "image/png", "标准拼写应该正确"
    print("  ✅ mimeType（标准）")
    
    # 备选拼写：mime_type
    result2 = {
        "content": [
            {"type": "image", "data": "BASE64" + "Y" * 100, "mime_type": "image/jpeg"}
        ]
    }
    _, images2 = multimodal.extract_from_result(result2)
    assert images2[0]["mime_type"] == "image/jpeg", "备选拼写应该正确"
    print("  ✅ mime_type（备选）")
    
    print("  ✅ MIME 类型变体通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("多模态处理 - 新格式兼容性测试")
    print("=" * 60)
    
    tests = [
        test_has_images_new_format_text_only,
        test_has_images_new_format_with_image,
        test_has_images_new_format_multiple_images,
        test_extract_from_result_new_format,
        test_extract_from_result_multiple_images,
        test_backward_compatibility_old_format,
        test_result_to_text_only_new_format,
        test_process_multimodal_messages_new_format,
        test_edge_cases,
        test_mime_type_variants,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ 所有测试通过！新格式兼容性验证成功。")
        return 0
    else:
        print(f"\n❌ {failed} 个测试失败，请检查修复。")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
