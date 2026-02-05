"""
Simple Summary 生成逻辑测试
"""

import pytest
from task_queue.utils.simple_summary import (
    generate_simple_summary,
    split_into_rounds,
    format_round_compressed,
    format_round_full,
    Round,
)


class TestSplitIntoRounds:
    """测试 split_into_rounds 函数"""
    
    def test_empty_context(self):
        """空 context 返回空列表"""
        assert split_into_rounds([]) == []
        assert split_into_rounds(None) == []
    
    def test_single_round_with_tool(self):
        """单轮带 tool 调用"""
        context = [
            {"role": "user", "content": "Hello"},
            {
                "role": "assistant",
                "content": "Let me think...",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {"name": "search", "arguments": '{"query": "test"}'},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "Search result"},
        ]
        
        rounds = split_into_rounds(context)
        assert len(rounds) == 1
        assert rounds[0].think == "Let me think..."
        assert len(rounds[0].tools) == 1
        assert rounds[0].tools[0]["name"] == "search"
        assert rounds[0].tools[0]["result"] == "Search result"
    
    def test_multiple_rounds(self):
        """多轮对话"""
        context = [
            {"role": "user", "content": "Question 1"},
            {
                "role": "assistant",
                "content": "Think 1",
                "tool_calls": [
                    {"id": "call_1", "function": {"name": "tool_a", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "Result 1"},
            {"role": "user", "content": "Question 2"},
            {
                "role": "assistant",
                "content": "Think 2",
                "tool_calls": [
                    {"id": "call_2", "function": {"name": "tool_b", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "call_2", "content": "Result 2"},
        ]
        
        rounds = split_into_rounds(context)
        assert len(rounds) == 2
        assert rounds[0].think == "Think 1"
        assert rounds[1].think == "Think 2"
        assert rounds[0].tools[0]["name"] == "tool_a"
        assert rounds[1].tools[0]["name"] == "tool_b"
    
    def test_assistant_without_tool_calls(self):
        """assistant 没有 tool_calls（纯回复）"""
        context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        
        rounds = split_into_rounds(context)
        assert len(rounds) == 1
        assert rounds[0].think == "Hi there!"
        assert len(rounds[0].tools) == 0
    
    def test_reasoning_content(self):
        """使用 reasoning_content 作为 think"""
        context = [
            {"role": "user", "content": "Hello"},
            {
                "role": "assistant",
                "reasoning_content": "Deep thought...",
                "content": "",
                "tool_calls": [
                    {"id": "call_1", "function": {"name": "test", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "OK"},
        ]
        
        rounds = split_into_rounds(context)
        assert len(rounds) == 1
        assert rounds[0].think == "Deep thought..."
    
    def test_multiple_tool_calls_in_one_round(self):
        """一轮中多个 tool 调用"""
        context = [
            {"role": "user", "content": "Do both"},
            {
                "role": "assistant",
                "content": "I'll do both",
                "tool_calls": [
                    {"id": "call_1", "function": {"name": "tool_a", "arguments": "{}"}},
                    {"id": "call_2", "function": {"name": "tool_b", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "Result A"},
            {"role": "tool", "tool_call_id": "call_2", "content": "Result B"},
        ]
        
        rounds = split_into_rounds(context)
        assert len(rounds) == 1
        assert len(rounds[0].tools) == 2
        assert rounds[0].tools[0]["result"] == "Result A"
        assert rounds[0].tools[1]["result"] == "Result B"


class TestFormatRounds:
    """测试轮次格式化函数"""
    
    def test_format_round_compressed(self):
        """测试压缩格式"""
        round = Round(
            index=0,
            think="This is my thinking",
            tools=[
                {
                    "id": "call_1",
                    "name": "search",
                    "args": '{"query":"test"}',
                    "result": "Very long result that should be replaced with reference",
                    "result_id": "call_1",
                },
            ],
        )
        
        output = format_round_compressed(round)
        assert "[Think] This is my thinking" in output
        assert "[Tool] search(" in output
        assert "[Result] → [task_result:call_1]" in output
        # 完整结果不应出现
        assert "Very long result" not in output
    
    def test_format_round_full(self):
        """测试完整格式"""
        round = Round(
            index=0,
            think="This is my thinking",
            tools=[
                {
                    "id": "call_1",
                    "name": "search",
                    "args": '{"query":"test"}',
                    "result": "Search result content",
                    "result_id": "call_1",
                },
            ],
        )
        
        output = format_round_full(round)
        assert "[Think] This is my thinking" in output
        assert "[Tool] search(" in output
        assert "[Result] Search result content" in output
        # 引用不应出现
        assert "task_result:" not in output


class TestGenerateSimpleSummary:
    """测试 generate_simple_summary 函数"""
    
    def test_empty_context(self):
        """空 context"""
        assert generate_simple_summary([]) == "[No context]"
        assert generate_simple_summary(None) == "[No context]"
    
    def test_no_rounds(self):
        """无轮次（只有 user 消息）"""
        context = [{"role": "user", "content": "Hello"}]
        assert generate_simple_summary(context) == "[No rounds found]"
    
    def test_last_three_rounds_full(self):
        """最后3轮完整保留"""
        # 创建5轮对话
        context = []
        for i in range(5):
            context.append({"role": "user", "content": f"Question {i+1}"})
            context.append({
                "role": "assistant",
                "content": f"Think {i+1}",
                "tool_calls": [
                    {"id": f"call_{i+1}", "function": {"name": f"tool_{i+1}", "arguments": "{}"}},
                ],
            })
            context.append({"role": "tool", "tool_call_id": f"call_{i+1}", "content": f"Result {i+1}"})
        
        summary = generate_simple_summary(context, recent_rounds=3)
        
        # 前2轮应该是压缩的（使用引用）
        assert "[task_result:call_1]" in summary
        assert "[task_result:call_2]" in summary
        
        # 后3轮应该是完整的（包含实际结果）
        assert "[Result] Result 3" in summary
        assert "[Result] Result 4" in summary
        assert "[Result] Result 5" in summary
    
    def test_less_than_three_rounds_all_full(self):
        """少于3轮全部保留完整"""
        context = [
            {"role": "user", "content": "Question"},
            {
                "role": "assistant",
                "content": "Think",
                "tool_calls": [
                    {"id": "call_1", "function": {"name": "tool", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "Full result here"},
        ]
        
        summary = generate_simple_summary(context)
        
        # 应该包含完整结果
        assert "[Result] Full result here" in summary
        # 不应包含引用
        assert "task_result:" not in summary
    
    def test_round_headers(self):
        """轮次标题格式"""
        context = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
        ]
        
        summary = generate_simple_summary(context)
        
        assert "=== Round 1/2 ===" in summary
        assert "=== Round 2/2 ===" in summary
    
    def test_custom_recent_rounds(self):
        """自定义保留轮次数"""
        # 创建5轮对话
        context = []
        for i in range(5):
            context.append({"role": "user", "content": f"Q{i+1}"})
            context.append({
                "role": "assistant",
                "content": f"Think {i+1}",
                "tool_calls": [
                    {"id": f"call_{i+1}", "function": {"name": f"tool", "arguments": "{}"}},
                ],
            })
            context.append({"role": "tool", "tool_call_id": f"call_{i+1}", "content": f"Result {i+1}"})
        
        # 只保留最后1轮完整
        summary = generate_simple_summary(context, recent_rounds=1)
        
        # 前4轮应该是压缩的
        assert "[task_result:call_1]" in summary
        assert "[task_result:call_4]" in summary
        
        # 只有最后1轮完整
        assert "[Result] Result 5" in summary


class TestEdgeCases:
    """边界情况测试"""
    
    def test_invalid_messages(self):
        """无效消息被忽略"""
        context = [
            None,
            {"invalid": "message"},
            {"role": ""},  # 空 role
            {"role": "user", "content": "Valid"},
            {"role": "assistant", "content": "Also valid"},
        ]
        
        rounds = split_into_rounds(context)
        # 应该只有1轮（有效的 assistant）
        assert len(rounds) == 1
    
    def test_orphan_tool_result(self):
        """孤立的 tool result（没有对应的 tool_call）"""
        context = [
            {"role": "user", "content": "Hello"},
            {"role": "tool", "tool_call_id": "orphan", "content": "Orphan result"},
            {"role": "assistant", "content": "Response"},
        ]
        
        rounds = split_into_rounds(context)
        # 孤立的 tool result 应该被忽略
        assert len(rounds) == 1
        assert len(rounds[0].tools) == 0
    
    def test_json_content_in_tool_result(self):
        """tool result 中的 JSON 内容"""
        context = [
            {"role": "user", "content": "Hello"},
            {
                "role": "assistant",
                "content": "Calling tool",
                "tool_calls": [
                    {"id": "call_1", "function": {"name": "api", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "call_1", "content": {"data": "value", "nested": {"key": 1}}},
        ]
        
        rounds = split_into_rounds(context)
        # JSON 内容应该被转换为字符串
        assert len(rounds) == 1
        assert "data" in rounds[0].tools[0]["result"]
