#!/usr/bin/env python3
"""
测试多模态消息顺序修复

验证：
1. 多个 tool results（包含图片）时，tool results 保持连续
2. 图片 user messages 添加到所有 tool results 之后
3. 符合 OpenAI/Moonshot API 要求
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import json
from task_queue.utils.context import sanitize_context, process_multimodal_messages


def test_multiple_tool_results_with_images():
    """测试多个 tool results（包含图片）的处理"""
    print("\n" + "=" * 70)
    print("测试：多个 tool results（包含图片）")
    print("=" * 70)
    
    # 模拟 3 个工具调用的场景
    messages = [
        {"role": "user", "content": "截图并列出文件"},
        {
            "role": "assistant",
            "tool_calls": [
                {"id": "screenshot:0", "function": {"name": "screenshot"}},
                {"id": "shell_exec:1", "function": {"name": "shell_exec"}},
                {"id": "browser_navigate:2", "function": {"name": "browser_navigate"}},
            ],
        },
        # screenshot tool result（包含图片）
        {
            "role": "tool",
            "tool_call_id": "screenshot:0",
            "name": "screenshot",
            "content": json.dumps({
                "success": True,
                "content": [
                    {"type": "text", "text": "Screenshot taken"},
                    {"type": "image", "data": "iVBORw0KGgo" + "A" * 600000, "mimeType": "image/png"}
                ]
            })
        },
        # shell_exec tool result
        {
            "role": "tool",
            "tool_call_id": "shell_exec:1",
            "name": "shell_exec",
            "content": json.dumps({
                "success": True,
                "content": [{"type": "text", "text": "file1.txt\nfile2.txt"}]
            })
        },
        # browser_navigate tool result
        {
            "role": "tool",
            "tool_call_id": "browser_navigate:2",
            "name": "browser_navigate",
            "content": json.dumps({
                "success": True,
                "content": [{"type": "text", "text": "Navigated to https://example.com"}]
            })
        },
    ]
    
    print(f"原始消息: {len(messages)} 条\n")
    
    # 处理
    sanitized = sanitize_context(messages)
    processed = process_multimodal_messages(sanitized, provider="openai")
    
    print(f"处理后消息: {len(processed)} 条\n")
    
    # 验证顺序
    print("=== 消息序列 ===")
    for i, msg in enumerate(processed):
        role = msg.get('role')
        tool_calls = msg.get('tool_calls', [])
        tool_call_id = msg.get('tool_call_id', '')
        content = msg.get('content', '')
        
        print(f"[{i}] role={role}", end='')
        
        if tool_calls:
            tc_ids = [tc.get('id') for tc in tool_calls]
            print(f", tool_calls={tc_ids}", end='')
        
        if tool_call_id:
            print(f", tool_call_id={tool_call_id}", end='')
        
        if isinstance(content, list):
            print(f", content=[{len(content)} items]", end='')
        
        print()
    
    # 验证 tool results 的连续性
    print(f"\n=== 验证 ===")
    
    assistant_idx = None
    for i, msg in enumerate(processed):
        if msg.get('role') == 'assistant' and msg.get('tool_calls'):
            assistant_idx = i
            break
    
    if assistant_idx is None:
        print("❌ 未找到 assistant with tool_calls")
        return False
    
    expected_tool_calls = [tc.get('id') for tc in processed[assistant_idx].get('tool_calls', [])]
    print(f"Expected tool_call_ids: {expected_tool_calls}")
    
    # 检查后续消息
    found_tool_results = []
    i = assistant_idx + 1
    while i < len(processed):
        msg = processed[i]
        if msg.get('role') == 'tool':
            found_tool_results.append(msg.get('tool_call_id'))
        else:
            # 遇到非 tool result，停止
            break
        i += 1
    
    print(f"Found tool_call_ids: {found_tool_results}")
    
    # 验证
    missing = set(expected_tool_calls) - set(found_tool_results)
    if missing:
        print(f"❌ 缺失: {missing}")
        return False
    
    extra = set(found_tool_results) - set(expected_tool_calls)
    if extra:
        print(f"❌ 多余: {extra}")
        return False
    
    print(f"✅ 所有 tool results 连续且完整")
    
    # 验证图片 user message 的位置
    image_msg_idx = None
    for i, msg in enumerate(processed):
        if msg.get('role') == 'user' and isinstance(msg.get('content'), list):
            for item in msg.get('content', []):
                if item.get('type') == 'image_url':
                    image_msg_idx = i
                    break
    
    if image_msg_idx:
        if image_msg_idx > assistant_idx + len(expected_tool_calls):
            print(f"✅ 图片 user message 在所有 tool results 之后（索引 {image_msg_idx}）")
        else:
            print(f"❌ 图片 user message 位置错误（索引 {image_msg_idx}）")
            return False
    
    return True


def test_single_tool_with_image():
    """测试单个 tool result（包含图片）"""
    print("\n" + "=" * 70)
    print("测试：单个 tool result（包含图片）")
    print("=" * 70)
    
    messages = [
        {"role": "user", "content": "截图"},
        {
            "role": "assistant",
            "tool_calls": [
                {"id": "screenshot:0", "function": {"name": "screenshot"}},
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "screenshot:0",
            "name": "screenshot",
            "content": json.dumps({
                "success": True,
                "content": [
                    {"type": "text", "text": "Screenshot taken"},
                    {"type": "image", "data": "iVBORw0KGgo" + "A" * 100000, "mimeType": "image/png"}
                ]
            })
        },
        {"role": "assistant", "content": "我看到了截图"}
    ]
    
    sanitized = sanitize_context(messages)
    processed = process_multimodal_messages(sanitized, provider="openai")
    
    print(f"处理后消息: {len(processed)} 条\n")
    
    # 验证顺序
    for i, msg in enumerate(processed):
        role = msg.get('role')
        tool_call_id = msg.get('tool_call_id', '')
        content = msg.get('content', '')
        
        print(f"[{i}] role={role}", end='')
        if tool_call_id:
            print(f", tool_call_id={tool_call_id}", end='')
        if isinstance(content, list):
            print(f", content=[{len(content)} items]", end='')
        print()
    
    # 验证顺序：assistant -> tool -> user(image) -> assistant
    if len(processed) >= 5:
        if (processed[1].get('role') == 'assistant' and
            processed[2].get('role') == 'tool' and
            processed[3].get('role') == 'user' and
            processed[4].get('role') == 'assistant'):
            print(f"\n✅ 单个工具顺序正确")
            return True
    
    print(f"\n❌ 顺序错误")
    return False


def main():
    """运行所有测试"""
    all_passed = True
    
    try:
        if not test_multiple_tool_results_with_images():
            all_passed = False
        
        if not test_single_tool_with_image():
            all_passed = False
        
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有测试通过")
        print("\n修复验证成功：")
        print("  1. 多个 tool results 保持连续")
        print("  2. 图片 user messages 在所有 tool results 之后")
        print("  3. 符合 OpenAI/Moonshot API 要求")
    else:
        print("❌ 部分测试失败")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
