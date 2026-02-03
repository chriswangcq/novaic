"""
Pytest Configuration and Fixtures

Provides common fixtures for testing the NovAIC Gateway v2.6 architecture.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Database
from db.schema import init_schema


# ==================== Event Loop ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== Database Fixtures ====================

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[Database, None]:
    """
    Create an in-memory SQLite database for testing.
    
    This fixture creates a fresh database for each test,
    with all tables initialized from schema.py.
    """
    # Use a temporary file (in-memory doesn't work well with aiosqlite)
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    database = Database(db_path)
    await database.connect()
    
    yield database
    
    await database.close()
    # Clean up temp file
    try:
        db_path.unlink()
    except:
        pass


@pytest_asyncio.fixture
async def db_with_agent(db: Database) -> AsyncGenerator[tuple, None]:
    """
    Database with a pre-created test agent.
    
    Returns:
        Tuple of (database, agent_id)
    """
    agent_id = "test-agent-001"
    
    # Insert a test agent (using correct schema columns)
    await db.execute("""
        INSERT INTO agents (id, name, setup_complete, vm_config, ports, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (agent_id, "Test Agent", 1, "{}", "{}"))
    await db.commit()
    
    yield db, agent_id


# ==================== Repository Fixtures ====================

@pytest_asyncio.fixture
async def runtime_repo(db: Database):
    """RuntimeRepository fixture."""
    from db.repositories.runtime import RuntimeRepository
    return RuntimeRepository(db)


@pytest_asyncio.fixture
async def message_repo(db: Database):
    """MessageRepository fixture."""
    from db.repositories.message import MessageRepository
    return MessageRepository(db)


@pytest_asyncio.fixture
async def agent_state_repo(db: Database):
    """AgentStateRepository fixture."""
    from db.repositories.agent_state import AgentStateRepository
    return AgentStateRepository(db)


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_sse_broadcaster():
    """Mock SSE broadcaster for testing Master."""
    broadcaster = MagicMock()
    broadcaster.broadcast_new_task = AsyncMock()
    broadcaster.broadcast = AsyncMock()
    return broadcaster


@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""
    def _create_response(
        content: str = None,
        tool_calls: list = None,
        is_done: bool = False
    ) -> Dict[str, Any]:
        response = {
            "id": "chatcmpl-test",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop" if is_done else "tool_calls" if tool_calls else "stop",
            }],
            "usage": {"total_tokens": 100},
        }
        
        if tool_calls:
            response["choices"][0]["message"]["tool_calls"] = [
                {
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": tc.get("name"),
                        "arguments": tc.get("arguments", "{}"),
                    }
                }
                for i, tc in enumerate(tool_calls)
            ]
        
        return response
    
    return _create_response


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession for HTTP calls."""
    session = MagicMock()
    session.get = AsyncMock()
    session.post = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock()
    return session


# ==================== Task Fixtures ====================

@pytest.fixture
def sample_think_task() -> Dict[str, Any]:
    """Sample think task for testing."""
    return {
        "id": "task-think-001",
        "agent_id": "test-agent-001",
        "subagent_id": "main-abc123",
        "round_id": "round-1",
        "task_type": "think",
        "args": {
            "context": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, how are you?"},
            ]
        },
        "status": "pending",
    }


@pytest.fixture
def sample_tool_call_task() -> Dict[str, Any]:
    """Sample tool_call task for testing."""
    return {
        "id": "task-tool-001",
        "agent_id": "test-agent-001",
        "subagent_id": "main-abc123",
        "round_id": "round-1",
        "mcpcall_id": "mc-1",
        "task_type": "tool_call",
        "tool_name": "memory_write",
        "args": {
            "key": "test_key",
            "value": "test_value",
        },
        "idempotency_key": "test-agent-001-main-abc123-round-1-mc-1",
        "status": "pending",
    }


@pytest.fixture
def sample_reply_task() -> Dict[str, Any]:
    """Sample reply task for testing."""
    return {
        "id": "task-reply-001",
        "agent_id": "test-agent-001",
        "subagent_id": "main-abc123",
        "round_id": "round-1",
        "mcpcall_id": "mc-2",
        "task_type": "reply",
        "args": {
            "content": "Hello! I'm doing well, thank you for asking.",
        },
        "status": "pending",
    }


# ==================== MCP Fixtures ====================

@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI application for MCP server testing."""
    from fastapi import FastAPI
    app = FastAPI()
    return app


# ==================== Environment Fixtures ====================

@pytest.fixture(autouse=True)
def test_environment(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("NOVAIC_DATA_DIR", "/tmp/novaic-test")
    monkeypatch.setenv("NOVAIC_DEBUG", "true")


# ==================== Helper Functions ====================

async def create_test_runtime(runtime_repo, agent_id: str, runtime_type: str = "main"):
    """Helper to create a test runtime."""
    if runtime_type == "main":
        return await runtime_repo.create_main_runtime(agent_id)
    else:
        return await runtime_repo.create_sub_runtime(
            agent_id, 
            parent_subagent_id="main-parent"
        )


async def create_test_message(db: Database, agent_id: str, content: str = "Test message"):
    """Helper to create a test message in inbox."""
    from datetime import datetime
    import uuid
    
    msg_id = f"msg-{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    
    await db.execute("""
        INSERT INTO chat_messages (id, agent_id, type, content, read, processed, timestamp)
        VALUES (?, ?, ?, ?, 0, 0, ?)
    """, (msg_id, agent_id, "USER_MESSAGE", content, now))
    await db.commit()
    
    return msg_id
