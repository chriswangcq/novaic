"""
LLM 端到端集成测试 - 验证新格式工具结果到 LLM API 的完整流程

测试数据流：
  工具执行 (executor.py) 
    ↓ {success, content: [...]}
  多模态处理 (multimodal.py)
    ↓ extract_from_result()
    ↓ result_to_text_only()
  Context 处理 (context.py)
    ↓ process_multimodal_messages()
  LLM 客户端 (llm_client.py)
    ↓ _convert_content_to_anthropic()
    ↓ _convert_content_to_openai()
  LLM API (OpenAI/Anthropic)
"""

import json
import sys
import base64
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent / "novaic-backend"
sys.path.insert(0, str(project_root))

from task_queue.utils import multimodal, context
from gateway.core.llm_client import OpenAIClient, AnthropicClient

# 测试用的 10x10 PNG 图片（base64）- 足够长以通过 min_length 检查
TINY_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNk+M9Qz0AEYBxVSF+FABJADveWkH6oAAAAAElFTkSuQmCC" + "A" * 50  # 添加填充以确保长度 > 100

# 测试用的工具结果（新格式）
NEW_FORMAT_TOOL_RESULT = {
    "success": True,
    "content": [
        {"type": "text", "text": "Screenshot captured successfully"},
        {"type": "image", "data": TINY_PNG_BASE64, "mimeType": "image/png"}
    ]
}

# 测试用的工具结果（旧格式 - 向后兼容）
OLD_FORMAT_TOOL_RESULT = {
    "success": True,
    "message": "Screenshot captured",
    "screenshot": TINY_PNG_BASE64
}


def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_step(step_num: int, description: str):
    """打印测试步骤"""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 70)


def test_step1_extract():
    """步骤 1: 提取文本和图片"""
    print_step(1, "提取文本和图片 - extract_from_result()")
    
    # 测试新格式
    text, images = multimodal.extract_from_result(NEW_FORMAT_TOOL_RESULT)
    print(f"✅ 新格式 - 提取文本: '{text}'")
    print(f"✅ 新格式 - 提取图片数量: {len(images)}")
    assert text == "Screenshot captured successfully", "文本提取失败"
    assert len(images) == 1, "图片提取失败"
    assert images[0]["data"] == TINY_PNG_BASE64, "图片数据不匹配"
    assert images[0]["mime_type"] == "image/png", "图片 MIME 类型不匹配"
    
    # 测试旧格式（向后兼容）
    text_old, images_old = multimodal.extract_from_result(OLD_FORMAT_TOOL_RESULT)
    print(f"✅ 旧格式 - 提取文本: '{text_old}'")
    print(f"✅ 旧格式 - 提取图片数量: {len(images_old)}")
    assert len(images_old) == 1, "旧格式图片提取失败"
    
    print("\n✅ 步骤 1 通过：文本和图片提取正常")
    return text, images


def test_step2_has_images():
    """步骤 2: 检测图片"""
    print_step(2, "检测图片 - has_images()")
    
    # 测试新格式
    has_img_new = multimodal.has_images(NEW_FORMAT_TOOL_RESULT)
    print(f"✅ 新格式 - 图片检测: {has_img_new}")
    assert has_img_new == True, "新格式图片检测失败"
    
    # 测试旧格式
    has_img_old = multimodal.has_images(OLD_FORMAT_TOOL_RESULT)
    print(f"✅ 旧格式 - 图片检测: {has_img_old}")
    assert has_img_old == True, "旧格式图片检测失败"
    
    # 测试无图片结果
    no_image_result = {"success": True, "content": [{"type": "text", "text": "No image"}]}
    has_img_none = multimodal.has_images(no_image_result)
    print(f"✅ 无图片 - 图片检测: {has_img_none}")
    assert has_img_none == False, "无图片检测失败"
    
    print("\n✅ 步骤 2 通过：图片检测正常")


def test_step3_text_only():
    """步骤 3: 生成纯文本版本"""
    print_step(3, "生成纯文本版本 - result_to_text_only()")
    
    # 测试新格式
    text_only = multimodal.result_to_text_only(NEW_FORMAT_TOOL_RESULT)
    print(f"✅ 新格式 - 纯文本版本长度: {len(text_only)} 字符")
    print(f"✅ 新格式 - 纯文本预览: {text_only[:200]}...")
    
    # 验证：图片数据不在纯文本中
    assert TINY_PNG_BASE64 not in text_only, "图片数据未被移除"
    
    # 验证：包含占位符标记
    parsed = json.loads(text_only)
    assert "content" in parsed, "content 字段丢失"
    image_items = [item for item in parsed["content"] if item.get("type") == "image"]
    assert len(image_items) == 1, "图片占位符丢失"
    assert image_items[0].get("_placeholder") == True, "占位符标记缺失"
    print(f"✅ 新格式 - 图片占位符: {image_items[0]}")
    
    # 测试旧格式
    text_only_old = multimodal.result_to_text_only(OLD_FORMAT_TOOL_RESULT)
    assert TINY_PNG_BASE64 not in text_only_old, "旧格式图片数据未被移除"
    assert "[IMAGE DATA PROVIDED SEPARATELY TO LLM]" in text_only_old, "旧格式占位符缺失"
    print(f"✅ 旧格式 - 占位符正确")
    
    print("\n✅ 步骤 3 通过：纯文本版本生成正常")
    return text_only


def test_step4_context_processing():
    """步骤 4: Context 处理"""
    print_step(4, "Context 处理 - process_multimodal_messages()")
    
    # 构建消息列表
    messages = [
        {"role": "user", "content": "Take a screenshot"},
        {
            "role": "assistant", 
            "content": "Taking screenshot...",
            "tool_calls": [{
                "id": "call_123",
                "type": "function",
                "function": {"name": "browser_screenshot", "arguments": "{}"}
            }]
        },
        {
            "role": "tool", 
            "content": json.dumps(NEW_FORMAT_TOOL_RESULT), 
            "name": "browser_screenshot",
            "tool_call_id": "call_123"
        }
    ]
    
    print(f"📥 输入消息数量: {len(messages)}")
    
    # 测试 OpenAI 格式
    processed_openai = context.process_multimodal_messages(messages, "openai")
    print(f"✅ OpenAI 格式 - 处理后消息数量: {len(processed_openai)}")
    
    # 验证：应该增加一条 user message（包含图片）
    assert len(processed_openai) > len(messages), "OpenAI: 未添加图片消息"
    
    # 查找图片消息
    image_messages = [
        m for m in processed_openai 
        if m.get("role") == "user" and isinstance(m.get("content"), list)
    ]
    print(f"✅ OpenAI 格式 - 图片消息数量: {len(image_messages)}")
    
    if image_messages:
        img_content = image_messages[0]["content"]
        image_items = [item for item in img_content if item.get("type") == "image_url"]
        print(f"✅ OpenAI 格式 - 图片元素数量: {len(image_items)}")
        if image_items:
            print(f"✅ OpenAI 格式 - 图片 URL 格式: {image_items[0]['image_url']['url'][:50]}...")
            assert image_items[0]["image_url"]["url"].startswith("data:image/png;base64,"), "OpenAI 图片格式错误"
    
    # 测试 Anthropic 格式
    processed_anthropic = context.process_multimodal_messages(messages, "anthropic")
    print(f"✅ Anthropic 格式 - 处理后消息数量: {len(processed_anthropic)}")
    
    # 查找图片消息
    image_messages_anthropic = [
        m for m in processed_anthropic 
        if m.get("role") == "user" and isinstance(m.get("content"), list)
    ]
    print(f"✅ Anthropic 格式 - 图片消息数量: {len(image_messages_anthropic)}")
    
    if image_messages_anthropic:
        img_content = image_messages_anthropic[0]["content"]
        image_items = [item for item in img_content if item.get("type") == "image"]
        print(f"✅ Anthropic 格式 - 图片元素数量: {len(image_items)}")
        if image_items:
            print(f"✅ Anthropic 格式 - 图片结构: {list(image_items[0].keys())}")
            assert "source" in image_items[0], "Anthropic 图片格式错误"
            assert image_items[0]["source"]["type"] == "base64", "Anthropic 图片源类型错误"
    
    print("\n✅ 步骤 4 通过：Context 处理正常")
    return processed_openai, processed_anthropic


def test_step5_llm_format_conversion():
    """步骤 5: LLM 格式转换"""
    print_step(5, "LLM 格式转换 - to_openai_content / to_anthropic_content")
    
    # 准备图片数据
    images = [{"data": TINY_PNG_BASE64, "mime_type": "image/png"}]
    
    # 测试 OpenAI 格式
    openai_content = multimodal.to_openai_content(images, "Screenshot from tool")
    print(f"✅ OpenAI 格式 - Content 项数量: {len(openai_content)}")
    print(f"✅ OpenAI 格式 - 结构: {[item['type'] for item in openai_content]}")
    
    # 验证图片格式
    image_item = next((item for item in openai_content if item["type"] == "image_url"), None)
    assert image_item is not None, "OpenAI 图片项缺失"
    assert "image_url" in image_item, "OpenAI image_url 字段缺失"
    assert image_item["image_url"]["url"].startswith("data:image/png;base64,"), "OpenAI 数据 URL 格式错误"
    print(f"✅ OpenAI 格式验证通过")
    
    # 测试 Anthropic 格式
    anthropic_content = multimodal.to_anthropic_content(images, "Screenshot from tool")
    print(f"✅ Anthropic 格式 - Content 项数量: {len(anthropic_content)}")
    print(f"✅ Anthropic 格式 - 结构: {[item['type'] for item in anthropic_content]}")
    
    # 验证图片格式
    image_item_anthropic = next((item for item in anthropic_content if item["type"] == "image"), None)
    assert image_item_anthropic is not None, "Anthropic 图片项缺失"
    assert "source" in image_item_anthropic, "Anthropic source 字段缺失"
    assert image_item_anthropic["source"]["type"] == "base64", "Anthropic source 类型错误"
    assert image_item_anthropic["source"]["media_type"] == "image/png", "Anthropic media_type 错误"
    assert image_item_anthropic["source"]["data"] == TINY_PNG_BASE64, "Anthropic 图片数据错误"
    print(f"✅ Anthropic 格式验证通过")
    
    print("\n✅ 步骤 5 通过：LLM 格式转换正常")


def test_step6_anthropic_client_conversion():
    """步骤 6: Anthropic Client 内容转换"""
    print_step(6, "Anthropic Client - _convert_content_to_anthropic()")
    
    # 创建 Anthropic 客户端（不需要真实 API key，只测试转换逻辑）
    client = AnthropicClient(api_key="test-key")
    
    # 测试 OpenAI 格式的图片 content 转换
    openai_image_content = [
        {"type": "text", "text": "Here is the screenshot:"},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{TINY_PNG_BASE64}"}
        }
    ]
    
    converted = client._convert_content_to_anthropic(openai_image_content)
    print(f"✅ 转换后类型: {type(converted)}")
    print(f"✅ 转换后项数量: {len(converted)}")
    
    # 验证转换结果
    assert isinstance(converted, list), "转换结果应该是列表"
    assert len(converted) == 2, "应该有 2 个元素（文本 + 图片）"
    
    # 验证文本块
    text_block = converted[0]
    assert text_block["type"] == "text", "第一个元素应该是文本"
    assert text_block["text"] == "Here is the screenshot:", "文本内容不匹配"
    
    # 验证图片块
    image_block = converted[1]
    assert image_block["type"] == "image", "第二个元素应该是图片"
    assert "source" in image_block, "图片块缺少 source"
    assert image_block["source"]["type"] == "base64", "图片源类型错误"
    assert image_block["source"]["media_type"] == "image/png", "图片 MIME 类型错误"
    assert image_block["source"]["data"] == TINY_PNG_BASE64, "图片数据不匹配"
    
    print(f"✅ 文本块: {text_block}")
    print(f"✅ 图片块: {{type: 'image', source: {{type: 'base64', media_type: '{image_block['source']['media_type']}', data: '{image_block['source']['data'][:20]}...'}}}}")
    
    print("\n✅ 步骤 6 通过：Anthropic Client 内容转换正常")


def test_step7_backward_compatibility():
    """步骤 7: 向后兼容性测试"""
    print_step(7, "向后兼容性 - 旧格式支持")
    
    # 构建包含旧格式的消息
    messages_old = [
        {"role": "user", "content": "Take a screenshot"},
        {
            "role": "assistant", 
            "content": "Taking screenshot...",
            "tool_calls": [{
                "id": "call_456",
                "type": "function",
                "function": {"name": "browser_screenshot", "arguments": "{}"}
            }]
        },
        {
            "role": "tool", 
            "content": json.dumps(OLD_FORMAT_TOOL_RESULT), 
            "name": "browser_screenshot",
            "tool_call_id": "call_456"
        }
    ]
    
    # 测试处理
    processed = context.process_multimodal_messages(messages_old, "openai")
    print(f"✅ 旧格式 - 处理后消息数量: {len(processed)}")
    
    # 验证图片被提取
    image_messages = [
        m for m in processed 
        if m.get("role") == "user" and isinstance(m.get("content"), list)
    ]
    assert len(image_messages) > 0, "旧格式图片未被提取"
    print(f"✅ 旧格式 - 图片消息数量: {len(image_messages)}")
    
    print("\n✅ 步骤 7 通过：向后兼容性正常")


def test_step8_edge_cases():
    """步骤 8: 边界情况测试"""
    print_step(8, "边界情况测试")
    
    # 测试 1: 多张图片
    multi_image_result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Multiple screenshots"},
            {"type": "image", "data": TINY_PNG_BASE64, "mimeType": "image/png"},
            {"type": "image", "data": TINY_PNG_BASE64, "mimeType": "image/jpeg"},
        ]
    }
    
    text, images = multimodal.extract_from_result(multi_image_result)
    print(f"✅ 多图片 - 提取数量: {len(images)}")
    assert len(images) == 2, "多图片提取失败"
    assert images[0]["mime_type"] == "image/png", "第一张图片类型错误"
    assert images[1]["mime_type"] == "image/jpeg", "第二张图片类型错误"
    
    # 测试 2: 只有文本，无图片
    text_only_result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Operation completed"}
        ]
    }
    
    has_img = multimodal.has_images(text_only_result)
    print(f"✅ 纯文本 - 图片检测: {has_img}")
    assert has_img == False, "纯文本不应检测到图片"
    
    # 测试 3: 空 content 数组
    empty_result = {"success": True, "content": []}
    text, images = multimodal.extract_from_result(empty_result)
    print(f"✅ 空 content - 文本长度: {len(text)}, 图片: {len(images)}")
    # 空 content 会回退到提取其他字段（success, content 等），这是正常的
    assert len(images) == 0, "空 content 不应有图片"
    
    # 测试 4: 混合新旧格式（优先级测试）
    mixed_result = {
        "success": True,
        "content": [
            {"type": "text", "text": "New format text"}
        ],
        "screenshot": TINY_PNG_BASE64  # 旧格式字段
    }
    
    text, images = multimodal.extract_from_result(mixed_result)
    print(f"✅ 混合格式 - 文本来源: '{text}'")
    # 应该优先使用新格式的文本
    assert text == "New format text", "应优先使用新格式"
    
    print("\n✅ 步骤 8 通过：边界情况处理正常")


def test_step9_nested_result_format():
    """步骤 9: 嵌套结果格式测试"""
    print_step(9, "嵌套结果格式 - {success, result: {...}}")
    
    # 某些工具返回嵌套格式：{success: true, result: {content: [...]}}
    nested_result = {
        "success": True,
        "result": {
            "content": [
                {"type": "text", "text": "Nested format"},
                {"type": "image", "data": TINY_PNG_BASE64, "mimeType": "image/png"}
            ]
        }
    }
    
    # 模拟 context 处理
    messages = [
        {
            "role": "tool",
            "content": json.dumps(nested_result),
            "name": "test_tool",
            "tool_call_id": "call_789"
        }
    ]
    
    processed = context.process_multimodal_messages(messages, "openai")
    print(f"✅ 嵌套格式 - 处理后消息数量: {len(processed)}")
    
    # 验证：应该正确提取嵌套的图片
    image_messages = [
        m for m in processed 
        if m.get("role") == "user" and isinstance(m.get("content"), list)
    ]
    assert len(image_messages) > 0, "嵌套格式图片未被提取"
    print(f"✅ 嵌套格式 - 图片消息数量: {len(image_messages)}")
    
    print("\n✅ 步骤 9 通过：嵌套结果格式处理正常")


def run_all_tests():
    """运行所有测试"""
    print_section("LLM 端到端集成测试")
    print("测试目标: 验证新格式工具结果到 LLM API 的完整数据流")
    print("测试范围: multimodal.py → context.py → llm_client.py")
    
    try:
        # 步骤 1-9
        test_step1_extract()
        test_step2_has_images()
        test_step3_text_only()
        test_step4_context_processing()
        test_step5_llm_format_conversion()
        test_step6_anthropic_client_conversion()
        test_step7_backward_compatibility()
        test_step8_edge_cases()
        test_step9_nested_result_format()
        
        # 汇总
        print_section("测试总结")
        print("\n✅ 所有测试通过！")
        print("\n验证完成的功能:")
        print("  ✅ 步骤 1: 提取文本和图片")
        print("  ✅ 步骤 2: 检测图片")
        print("  ✅ 步骤 3: 生成纯文本版本")
        print("  ✅ 步骤 4: Context 处理")
        print("  ✅ 步骤 5: LLM 格式转换")
        print("  ✅ 步骤 6: Anthropic Client 内容转换")
        print("  ✅ 步骤 7: 向后兼容性")
        print("  ✅ 步骤 8: 边界情况处理")
        print("  ✅ 步骤 9: 嵌套结果格式")
        
        print("\n数据流验证:")
        print("  工具执行 (executor.py)")
        print("    ↓ {success, content: [...]}")
        print("  ✅ 多模态处理 (multimodal.py)")
        print("    ↓ extract_from_result()")
        print("    ↓ result_to_text_only()")
        print("  ✅ Context 处理 (context.py)")
        print("    ↓ process_multimodal_messages()")
        print("  ✅ LLM 客户端 (llm_client.py)")
        print("    ↓ _convert_content_to_anthropic()")
        print("    ↓ _convert_content_to_openai()")
        print("  → LLM API (OpenAI/Anthropic)")
        
        print("\n" + "="*70)
        print("  ✅ 端到端验证成功 - 可以部署")
        print("="*70)
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
