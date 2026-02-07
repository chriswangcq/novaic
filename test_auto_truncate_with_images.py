"""
自动截断与图片集成测试

验证图片数据不会被自动截断机制截断。
"""

import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent / "novaic-backend"
sys.path.insert(0, str(project_root))

from task_queue.utils import multimodal, context

# 生成一个大的 base64 字符串（模拟大图片）
LARGE_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9" + "A" * 10000  # 10KB+

# 生成一个非常长的文本
LARGE_TEXT = "This is a very long text. " * 1000  # ~26KB


def test_image_not_truncated():
    """测试图片数据不会被截断"""
    print("\n" + "="*70)
    print("  测试：图片数据不会被自动截断")
    print("="*70)
    
    # 构建包含大图片的结果
    large_image_result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Large screenshot"},
            {"type": "image", "data": LARGE_IMAGE_BASE64, "mimeType": "image/png"}
        ]
    }
    
    # 提取图片
    text, images = multimodal.extract_from_result(large_image_result)
    print(f"\n✅ 原始图片大小: {len(LARGE_IMAGE_BASE64)} 字符")
    print(f"✅ 提取后图片大小: {len(images[0]['data'])} 字符")
    
    # 验证图片数据完整
    assert images[0]["data"] == LARGE_IMAGE_BASE64, "图片数据被修改"
    print(f"✅ 图片数据完整性验证通过")
    
    # 生成纯文本版本
    text_only = multimodal.result_to_text_only(large_image_result)
    print(f"✅ 纯文本版本长度: {len(text_only)} 字符")
    
    # 验证纯文本版本不包含完整图片数据
    assert LARGE_IMAGE_BASE64 not in text_only, "纯文本版本不应包含完整图片"
    print(f"✅ 纯文本版本正确（图片被占位符替换）")
    
    # Context 处理
    messages = [
        {"role": "user", "content": "Take a screenshot"},
        {
            "role": "assistant",
            "content": "Taking...",
            "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "screenshot", "arguments": "{}"}
            }]
        },
        {
            "role": "tool",
            "content": json.dumps(large_image_result),
            "name": "screenshot",
            "tool_call_id": "call_1"
        }
    ]
    
    processed = context.process_multimodal_messages(messages, "openai")
    print(f"✅ Context 处理后消息数量: {len(processed)}")
    
    # 查找图片消息
    image_messages = [
        m for m in processed
        if m.get("role") == "user" and isinstance(m.get("content"), list)
    ]
    
    if image_messages:
        img_content = image_messages[0]["content"]
        image_items = [item for item in img_content if item.get("type") == "image_url"]
        if image_items:
            # 提取 base64 数据（去除 data URL 前缀）
            data_url = image_items[0]["image_url"]["url"]
            if "base64," in data_url:
                extracted_data = data_url.split("base64,")[1]
                print(f"✅ 传递给 LLM 的图片大小: {len(extracted_data)} 字符")
                assert extracted_data == LARGE_IMAGE_BASE64, "传递给 LLM 的图片数据不完整"
                print(f"✅ 传递给 LLM 的图片数据完整")
    
    print("\n" + "="*70)
    print("  ✅ 图片数据不会被截断 - 测试通过")
    print("="*70)


def test_text_with_image():
    """测试包含文本和图片的结果"""
    print("\n" + "="*70)
    print("  测试：长文本 + 图片的混合处理")
    print("="*70)
    
    mixed_result = {
        "success": True,
        "content": [
            {"type": "text", "text": LARGE_TEXT},
            {"type": "image", "data": LARGE_IMAGE_BASE64, "mimeType": "image/png"}
        ]
    }
    
    # 提取
    text, images = multimodal.extract_from_result(mixed_result)
    print(f"\n✅ 提取的文本长度: {len(text)} 字符")
    print(f"✅ 提取的图片数量: {len(images)}")
    
    # 验证文本完整
    assert text == LARGE_TEXT, "文本被修改"
    print(f"✅ 文本完整性验证通过")
    
    # 验证图片完整
    assert images[0]["data"] == LARGE_IMAGE_BASE64, "图片被修改"
    print(f"✅ 图片完整性验证通过")
    
    # 生成纯文本版本
    text_only = multimodal.result_to_text_only(mixed_result)
    parsed = json.loads(text_only)
    
    # 验证文本保留
    text_items = [item for item in parsed["content"] if item.get("type") == "text"]
    assert len(text_items) > 0, "文本丢失"
    assert text_items[0]["text"] == LARGE_TEXT, "文本在纯文本版本中被修改"
    print(f"✅ 纯文本版本中的文本完整")
    
    # 验证图片被占位符替换
    image_items = [item for item in parsed["content"] if item.get("type") == "image"]
    assert len(image_items) > 0, "图片占位符丢失"
    assert image_items[0].get("_placeholder") == True, "图片占位符标记缺失"
    assert LARGE_IMAGE_BASE64 not in text_only, "图片数据未被移除"
    print(f"✅ 图片被正确替换为占位符")
    
    print("\n" + "="*70)
    print("  ✅ 长文本 + 图片混合处理 - 测试通过")
    print("="*70)


def test_multiple_large_images():
    """测试多张大图片"""
    print("\n" + "="*70)
    print("  测试：多张大图片处理")
    print("="*70)
    
    multi_image_result = {
        "success": True,
        "content": [
            {"type": "text", "text": "Multiple screenshots"},
            {"type": "image", "data": LARGE_IMAGE_BASE64, "mimeType": "image/png"},
            {"type": "image", "data": LARGE_IMAGE_BASE64 + "X", "mimeType": "image/jpeg"},
        ]
    }
    
    # 提取
    text, images = multimodal.extract_from_result(multi_image_result)
    print(f"\n✅ 提取的图片数量: {len(images)}")
    
    # 验证所有图片完整
    assert len(images) == 2, "图片数量不对"
    assert images[0]["data"] == LARGE_IMAGE_BASE64, "第一张图片被修改"
    assert images[1]["data"] == LARGE_IMAGE_BASE64 + "X", "第二张图片被修改"
    print(f"✅ 所有图片完整性验证通过")
    
    # Context 处理
    messages = [
        {
            "role": "tool",
            "content": json.dumps(multi_image_result),
            "name": "test_tool",
            "tool_call_id": "call_1"
        }
    ]
    
    processed = context.process_multimodal_messages(messages, "openai")
    
    # 查找图片消息
    image_messages = [
        m for m in processed
        if m.get("role") == "user" and isinstance(m.get("content"), list)
    ]
    
    assert len(image_messages) > 0, "图片消息缺失"
    img_content = image_messages[0]["content"]
    image_items = [item for item in img_content if item.get("type") == "image_url"]
    print(f"✅ 传递给 LLM 的图片数量: {len(image_items)}")
    assert len(image_items) == 2, "传递给 LLM 的图片数量不对"
    
    print("\n" + "="*70)
    print("  ✅ 多张大图片处理 - 测试通过")
    print("="*70)


def run_all_tests():
    """运行所有自动截断与图片集成测试"""
    print("\n" + "="*70)
    print("  自动截断与图片集成测试")
    print("="*70)
    print("测试目标: 验证图片数据不会被自动截断")
    
    try:
        test_image_not_truncated()
        test_text_with_image()
        test_multiple_large_images()
        
        print("\n" + "="*70)
        print("  ✅ 所有自动截断与图片集成测试通过")
        print("="*70)
        print("\n关键验证:")
        print("  ✅ 图片数据完整传递（不被截断）")
        print("  ✅ 长文本 + 图片混合处理正确")
        print("  ✅ 多张大图片处理正确")
        print("  ✅ 纯文本版本生成正确（图片占位符）")
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
