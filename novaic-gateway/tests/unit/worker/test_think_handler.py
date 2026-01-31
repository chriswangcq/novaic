"""
Unit Tests for Think Handler

Tests the Worker's think task handling:
- LLM configuration retrieval
- Context processing
- Action parsing (tool_call, reply, done)
- Error handling
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class MockResponse:
    """Mock aiohttp response."""
    def __init__(self, status: int, data: dict):
        self.status = status
        self._data = data
    
    async def json(self):
        return self._data
    
    async def text(self):
        return json.dumps(self._data)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass


class TestHandleThinkBasic:
    """Basic tests for handle_think function."""
    
    @pytest.fixture
    def mock_llm_config(self):
        """Standard LLM configuration."""
        return {
            "model": "gpt-4o",
            "api_keys": [{
                "api_key": "test-key",
                "api_base": "https://api.openai.com/v1",
                "provider": "openai",
            }],
        }
    
    @pytest.fixture
    def mock_llm_result(self):
        """Mock LLM thinking result."""
        from worker.llm_caller import ThinkingResult, AgentAction, ActionType
        return ThinkingResult(
            actions=[
                AgentAction(type=ActionType.REPLY, content="Hello!"),
            ],
            reasoning="Responding to user greeting",
            is_final=True,
        )
    
    @pytest.mark.asyncio
    async def test_returns_success_with_actions(self, sample_think_task, mock_llm_config, mock_llm_result):
        """handle_think returns success with parsed actions."""
        with patch('worker.think_handler.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.get = MagicMock(return_value=MockResponse(200, mock_llm_config))
            mock_session.post = MagicMock(return_value=MockResponse(200, {}))
            mock_session_class.return_value = mock_session
            
            with patch('worker.think_handler.LLMCaller') as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.initialize = AsyncMock()
                mock_llm.set_system_prompt = MagicMock()
                mock_llm.add_user_message = MagicMock()
                mock_llm.add_assistant_message = MagicMock()
                mock_llm.add_tool_result = MagicMock()
                mock_llm.think = AsyncMock(return_value=mock_llm_result)
                mock_llm_class.return_value = mock_llm
                
                from worker.think_handler import handle_think
                result = await handle_think(sample_think_task, "http://test:9527")
        
        assert result["success"] is True
        assert len(result["actions"]) == 1
        assert result["actions"][0]["type"] == "reply"
        assert result["actions"][0]["content"] == "Hello!"
        assert result["is_final"] is True
    
    @pytest.mark.asyncio
    async def test_returns_tool_call_actions(self, sample_think_task, mock_llm_config):
        """handle_think correctly returns tool_call actions."""
        from worker.llm_caller import ThinkingResult, AgentAction, ActionType
        
        tool_call_result = ThinkingResult(
            actions=[
                AgentAction(
                    type=ActionType.TOOL_CALL,
                    tool_name="memory_write",
                    args={"key": "test", "value": "data"},
                ),
            ],
            reasoning="Need to store data",
            is_final=False,
        )
        
        with patch('worker.think_handler.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.get = MagicMock(return_value=MockResponse(200, mock_llm_config))
            mock_session.post = MagicMock(return_value=MockResponse(200, {}))
            mock_session_class.return_value = mock_session
            
            with patch('worker.think_handler.LLMCaller') as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.initialize = AsyncMock()
                mock_llm.set_system_prompt = MagicMock()
                mock_llm.add_user_message = MagicMock()
                mock_llm.think = AsyncMock(return_value=tool_call_result)
                mock_llm_class.return_value = mock_llm
                
                from worker.think_handler import handle_think
                result = await handle_think(sample_think_task, "http://test:9527")
        
        assert result["success"] is True
        assert result["actions"][0]["type"] == "tool_call"
        assert result["actions"][0]["tool"] == "memory_write"
        assert result["actions"][0]["args"]["key"] == "test"
        assert result["is_final"] is False
    
    @pytest.mark.asyncio
    async def test_handles_no_api_keys(self, sample_think_task):
        """handle_think returns error when no API keys configured."""
        no_keys_config = {
            "model": "gpt-4o",
            "api_keys": [],
        }
        
        with patch('worker.think_handler.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.get = MagicMock(return_value=MockResponse(200, no_keys_config))
            mock_session_class.return_value = mock_session
            
            from worker.think_handler import handle_think
            result = await handle_think(sample_think_task, "http://test:9527")
        
        assert result["success"] is False
        assert "No API keys" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handles_llm_exception(self, sample_think_task, mock_llm_config):
        """handle_think returns error on LLM exception."""
        with patch('worker.think_handler.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.get = MagicMock(return_value=MockResponse(200, mock_llm_config))
            mock_session.post = MagicMock(return_value=MockResponse(200, {}))
            mock_session_class.return_value = mock_session
            
            with patch('worker.think_handler.LLMCaller') as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.initialize = AsyncMock()
                mock_llm.set_system_prompt = MagicMock()
                mock_llm.add_user_message = MagicMock()
                mock_llm.think = AsyncMock(side_effect=Exception("API Error"))
                mock_llm_class.return_value = mock_llm
                
                from worker.think_handler import handle_think
                result = await handle_think(sample_think_task, "http://test:9527")
        
        assert result["success"] is False
        assert "error" in result


class TestContextProcessing:
    """Tests for context message processing."""
    
    @pytest.fixture
    def llm_config(self):
        return {
            "model": "gpt-4o",
            "api_keys": [{
                "api_key": "test-key",
                "api_base": "https://api.openai.com/v1",
                "provider": "openai",
            }],
        }
    
    @pytest.mark.asyncio
    async def test_adds_user_messages(self, llm_config):
        """User messages are added to LLM context."""
        task = {
            "id": "task-1",
            "agent_id": "agent-1",
            "subagent_id": "main-123",
            "round_id": "round-1",
            "args": {
                "context": [
                    {"role": "user", "content": "Hello"},
                    {"role": "user", "content": "How are you?"},
                ]
            },
        }
        
        from worker.llm_caller import ThinkingResult, AgentAction, ActionType
        mock_result = ThinkingResult(
            actions=[AgentAction(type=ActionType.REPLY, content="Hi")],
            reasoning="",
            is_final=True,
        )
        
        with patch('worker.think_handler.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.get = MagicMock(return_value=MockResponse(200, llm_config))
            mock_session.post = MagicMock(return_value=MockResponse(200, {}))
            mock_session_class.return_value = mock_session
            
            with patch('worker.think_handler.LLMCaller') as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.initialize = AsyncMock()
                mock_llm.set_system_prompt = MagicMock()
                mock_llm.add_user_message = MagicMock()
                mock_llm.add_assistant_message = MagicMock()
                mock_llm.add_tool_result = MagicMock()
                mock_llm.think = AsyncMock(return_value=mock_result)
                mock_llm_class.return_value = mock_llm
                
                from worker.think_handler import handle_think
                await handle_think(task, "http://test:9527")
                
                # Verify add_user_message was called
                assert mock_llm.add_user_message.call_count == 2
    
    @pytest.mark.asyncio
    async def test_adds_assistant_messages(self, llm_config):
        """Assistant messages are added to LLM context."""
        task = {
            "id": "task-1",
            "agent_id": "agent-1",
            "subagent_id": "main-123",
            "round_id": "round-1",
            "args": {
                "context": [
                    {"role": "assistant", "content": "Previous response"},
                ]
            },
        }
        
        from worker.llm_caller import ThinkingResult, AgentAction, ActionType
        mock_result = ThinkingResult(
            actions=[AgentAction(type=ActionType.REPLY, content="Hi")],
            reasoning="",
            is_final=True,
        )
        
        with patch('worker.think_handler.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.get = MagicMock(return_value=MockResponse(200, llm_config))
            mock_session.post = MagicMock(return_value=MockResponse(200, {}))
            mock_session_class.return_value = mock_session
            
            with patch('worker.think_handler.LLMCaller') as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.initialize = AsyncMock()
                mock_llm.set_system_prompt = MagicMock()
                mock_llm.add_user_message = MagicMock()
                mock_llm.add_assistant_message = MagicMock()
                mock_llm.add_tool_result = MagicMock()
                mock_llm.think = AsyncMock(return_value=mock_result)
                mock_llm_class.return_value = mock_llm
                
                from worker.think_handler import handle_think
                await handle_think(task, "http://test:9527")
                
                mock_llm.add_assistant_message.assert_called_with("Previous response")


class TestBroadcasting:
    """Tests for status broadcasting."""
    
    @pytest.fixture
    def mock_llm_config(self):
        return {
            "model": "gpt-4o",
            "api_keys": [{
                "api_key": "test-key",
                "api_base": "https://api.openai.com/v1",
                "provider": "openai",
            }],
        }
    
    @pytest.mark.asyncio
    async def test_broadcasts_thinking_status(self, sample_think_task, mock_llm_config):
        """handle_think broadcasts thinking status."""
        from worker.llm_caller import ThinkingResult, AgentAction, ActionType
        mock_result = ThinkingResult(
            actions=[AgentAction(type=ActionType.REPLY, content="Hi")],
            reasoning="",
            is_final=True,
        )
        
        post_calls = []
        
        with patch('worker.think_handler.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.get = MagicMock(return_value=MockResponse(200, mock_llm_config))
            
            # Track post calls
            async def track_post(url, *args, **kwargs):
                post_calls.append(url)
                return MockResponse(200, {})
            mock_session.post = track_post
            mock_session_class.return_value = mock_session
            
            with patch('worker.think_handler.LLMCaller') as mock_llm_class:
                mock_llm = MagicMock()
                mock_llm.initialize = AsyncMock()
                mock_llm.set_system_prompt = MagicMock()
                mock_llm.add_user_message = MagicMock()
                mock_llm.think = AsyncMock(return_value=mock_result)
                mock_llm_class.return_value = mock_llm
                
                from worker.think_handler import handle_think
                await handle_think(sample_think_task, "http://test:9527")
        
        # Should have made some post calls (broadcasting)
        assert len(post_calls) >= 1
