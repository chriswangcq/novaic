"""
Context Builder 单元测试

测试新 Runtime 启动时的 Context 构建逻辑。
"""

import pytest
from unittest.mock import Mock, patch


class TestBuildInitialContext:
    """测试 build_initial_context 函数"""
    
    def test_empty_subagent_no_history(self):
        """空 SubAgent，没有历史"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": None,
        }
        mock_client.get_hrl.return_value = {"hrl": [], "length": 0}
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        assert context == []
    
    def test_only_historical_summary(self):
        """只有 historical_summary，没有 HRL"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": "This is the merged history of past work.",
        }
        mock_client.get_hrl.return_value = {"hrl": [], "length": 0}
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        assert len(context) == 1
        assert context[0]["role"] == "system"
        assert "[历史记忆]" in context[0]["content"]
        assert "This is the merged history" in context[0]["content"]
    
    def test_hrl_less_than_5_uses_hot_summary(self):
        """HRL < 5，全部使用 hot_summary"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": None,
        }
        mock_client.get_hrl.return_value = {
            "hrl": ["rt-1", "rt-2", "rt-3"],
            "length": 3
        }
        mock_client.get_runtimes_by_ids.return_value = [
            {"runtime_id": "rt-1", "hot_summary": "Hot 1", "cold_summary": None, "simple_summary": "Simple 1"},
            {"runtime_id": "rt-2", "hot_summary": "Hot 2", "cold_summary": None, "simple_summary": "Simple 2"},
            {"runtime_id": "rt-3", "hot_summary": None, "cold_summary": None, "simple_summary": "Simple 3"},
        ]
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        assert len(context) == 1
        assert context[0]["role"] == "system"
        assert "[最近的工作记录]" in context[0]["content"]
        assert "Hot 1" in context[0]["content"]
        assert "Hot 2" in context[0]["content"]
        assert "Simple 3" in context[0]["content"]  # Fallback to simple
    
    def test_hrl_more_than_5_splits_older_and_recent(self):
        """HRL > 5，分割为 older 和 recent"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": "History",
        }
        mock_client.get_hrl.return_value = {
            "hrl": ["rt-1", "rt-2", "rt-3", "rt-4", "rt-5", "rt-6", "rt-7"],
            "length": 7
        }
        mock_client.get_runtimes_by_ids.return_value = [
            {"runtime_id": "rt-1", "hot_summary": "Hot 1", "cold_summary": "Cold 1", "simple_summary": "Simple 1"},
            {"runtime_id": "rt-2", "hot_summary": "Hot 2", "cold_summary": "Cold 2", "simple_summary": "Simple 2"},
            {"runtime_id": "rt-3", "hot_summary": "Hot 3", "cold_summary": "Cold 3", "simple_summary": "Simple 3"},
            {"runtime_id": "rt-4", "hot_summary": "Hot 4", "cold_summary": "Cold 4", "simple_summary": "Simple 4"},
            {"runtime_id": "rt-5", "hot_summary": "Hot 5", "cold_summary": "Cold 5", "simple_summary": "Simple 5"},
            {"runtime_id": "rt-6", "hot_summary": "Hot 6", "cold_summary": "Cold 6", "simple_summary": "Simple 6"},
            {"runtime_id": "rt-7", "hot_summary": "Hot 7", "cold_summary": "Cold 7", "simple_summary": "Simple 7"},
        ]
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        # Should have 3 parts: historical_summary, older (cold), recent (hot)
        assert len(context) == 3
        
        # Part 1: Historical summary
        assert "[历史记忆]" in context[0]["content"]
        assert "History" in context[0]["content"]
        
        # Part 2: Older runtimes (rt-1, rt-2) using cold_summary
        assert "[较早的工作记录]" in context[1]["content"]
        assert "Cold 1" in context[1]["content"]
        assert "Cold 2" in context[1]["content"]
        
        # Part 3: Recent runtimes (rt-3 to rt-7) using hot_summary
        assert "[最近的工作记录]" in context[2]["content"]
        assert "Hot 3" in context[2]["content"]
        assert "Hot 7" in context[2]["content"]
    
    def test_fallback_to_simple_when_no_cold(self):
        """没有 cold_summary 时回退到 simple_summary"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": None,
        }
        mock_client.get_hrl.return_value = {
            "hrl": ["rt-1", "rt-2", "rt-3", "rt-4", "rt-5", "rt-6"],
            "length": 6
        }
        mock_client.get_runtimes_by_ids.return_value = [
            {"runtime_id": "rt-1", "hot_summary": None, "cold_summary": None, "simple_summary": "Simple 1"},
            {"runtime_id": "rt-2", "hot_summary": None, "cold_summary": None, "simple_summary": "Simple 2"},
            {"runtime_id": "rt-3", "hot_summary": None, "cold_summary": None, "simple_summary": "Simple 3"},
            {"runtime_id": "rt-4", "hot_summary": None, "cold_summary": None, "simple_summary": "Simple 4"},
            {"runtime_id": "rt-5", "hot_summary": None, "cold_summary": None, "simple_summary": "Simple 5"},
            {"runtime_id": "rt-6", "hot_summary": None, "cold_summary": None, "simple_summary": "Simple 6"},
        ]
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        # Should have 2 parts: older and recent (no historical_summary)
        assert len(context) == 2
        
        # Older (rt-1) uses simple_summary as fallback
        assert "[较早的工作记录]" in context[0]["content"]
        assert "Simple 1" in context[0]["content"]
        
        # Recent (rt-2 to rt-6) uses simple_summary as fallback
        assert "[最近的工作记录]" in context[1]["content"]
        assert "Simple 2" in context[1]["content"]
    
    def test_missing_runtime_in_map(self):
        """HRL 中的 runtime_id 不在返回结果中"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": None,
        }
        mock_client.get_hrl.return_value = {
            "hrl": ["rt-1", "rt-2", "rt-missing"],
            "length": 3
        }
        # rt-missing not in results
        mock_client.get_runtimes_by_ids.return_value = [
            {"runtime_id": "rt-1", "hot_summary": "Hot 1", "cold_summary": None, "simple_summary": None},
            {"runtime_id": "rt-2", "hot_summary": "Hot 2", "cold_summary": None, "simple_summary": None},
        ]
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        # Should skip missing runtime
        assert len(context) == 1
        assert "Hot 1" in context[0]["content"]
        assert "Hot 2" in context[0]["content"]
    
    def test_subagent_fetch_error(self):
        """获取 SubAgent 失败"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.side_effect = Exception("Network error")
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        assert context == []
    
    def test_hrl_fetch_error(self):
        """获取 HRL 失败，仍返回 historical_summary"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": "History content",
        }
        mock_client.get_hrl.side_effect = Exception("HRL error")
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        # Should still have historical_summary
        assert len(context) == 1
        assert "History content" in context[0]["content"]
    
    def test_runtimes_fetch_error(self):
        """获取 runtimes 失败，仍返回 historical_summary"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": "History content",
        }
        mock_client.get_hrl.return_value = {"hrl": ["rt-1"], "length": 1}
        mock_client.get_runtimes_by_ids.side_effect = Exception("Runtimes error")
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        # Should still have historical_summary
        assert len(context) == 1
        assert "History content" in context[0]["content"]


class TestBuildContextSummary:
    """测试 build_context_summary 函数"""
    
    def test_returns_stats(self):
        """返回统计信息"""
        from task_queue.utils.context_builder import build_context_summary
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": "History",
        }
        mock_client.get_hrl.return_value = {"hrl": ["rt-1", "rt-2"], "length": 2}
        mock_client.get_runtimes_by_ids.return_value = [
            {"runtime_id": "rt-1", "hot_summary": "Hot 1", "cold_summary": None, "simple_summary": None},
            {"runtime_id": "rt-2", "hot_summary": "Hot 2", "cold_summary": None, "simple_summary": None},
        ]
        
        result = build_context_summary("agent-1", "main", mock_client)
        
        assert "context" in result
        assert "stats" in result
        assert result["stats"]["has_historical_summary"] == True
        assert result["stats"]["total_parts"] == 2  # history + recent


class TestContextBuilderIntegration:
    """集成测试（需要实际数据）"""
    
    def test_separator_format(self):
        """验证分隔符格式"""
        from task_queue.utils.context_builder import build_initial_context
        
        mock_client = Mock()
        mock_client.get_subagent.return_value = {
            "subagent_id": "main",
            "agent_id": "agent-1",
            "historical_summary": None,
        }
        mock_client.get_hrl.return_value = {"hrl": ["rt-1", "rt-2"], "length": 2}
        mock_client.get_runtimes_by_ids.return_value = [
            {"runtime_id": "rt-1", "hot_summary": "Summary A", "cold_summary": None, "simple_summary": None},
            {"runtime_id": "rt-2", "hot_summary": "Summary B", "cold_summary": None, "simple_summary": None},
        ]
        
        context = build_initial_context("agent-1", "main", mock_client)
        
        # Summaries should be separated by "---"
        assert len(context) == 1
        content = context[0]["content"]
        assert "Summary A" in content
        assert "---" in content
        assert "Summary B" in content
