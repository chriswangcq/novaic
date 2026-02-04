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

from gateway.db.database import Database
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from task_queue.instance import init_task_queue, init_saga_orchestrator, set_handler_context, shutdown_task_queue, get_handler_context
from task_queue.routes import (
    create_task_queue_router,
    create_handler_router,
    create_business_router,
    create_recovery_router,
)
from gateway.api.internal import router as internal_router
import gateway.db.database as db_module


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


class TestGatewayClient:
    """Gateway internal API client for tests (ASGI-backed)."""

    def __init__(self, app: FastAPI):
        self._app = app

    async def _request(self, method: str, path: str, json_data: Dict[str, Any] = None) -> Dict[str, Any]:
        async with AsyncClient(transport=ASGITransport(app=self._app), base_url="http://test") as client:
            resp = await client.request(method, path, json=json_data)
            resp.raise_for_status()
            return resp.json()

    async def get_runtime(self, runtime_id: str):
        data = await self._request("GET", f"/internal/runtimes/{runtime_id}")
        return data.get("runtime")

    async def create_runtime(self, agent_id: str, subagent_id: str, initial_context=None):
        return await self._request("POST", "/internal/runtimes", {
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "initial_context": initial_context or [],
        })

    async def update_runtime(self, runtime_id: str, data: Dict[str, Any]):
        return await self._request("PATCH", f"/internal/runtimes/{runtime_id}", data)

    async def claim_phase(self, runtime_id: str, expected_phase: str, new_phase: str, round_id: str = None):
        payload = {"expected_phase": expected_phase, "new_phase": new_phase}
        if round_id:
            payload["round_id"] = round_id
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/claim-phase", payload)

    async def advance_round(self, runtime_id: str, expected_round_num: int = None):
        payload = {"expected_round_num": expected_round_num} if expected_round_num is not None else {}
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/advance", payload)

    async def get_subagent_runtime(self, agent_id: str, subagent_id: str):
        data = await self._request("GET", f"/internal/runtimes/subagent/{agent_id}/{subagent_id}")
        return data.get("runtime")

    async def append_context(self, runtime_id: str, message: Dict[str, Any], message_type: str, round_id: str, idempotency_key: str):
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/context/append", {
            "message": message,
            "message_type": message_type,
            "round_id": round_id,
            "idempotency_key": idempotency_key,
        })

    async def claim_message(self, message_id: str):
        return await self._request("POST", f"/internal/messages/{message_id}/claim", {})

    async def has_new_messages(self, agent_id: str):
        return await self._request("GET", f"/internal/messages/has-new/{agent_id}")

    async def get_unread_sent_messages(self, agent_id: str):
        data = await self._request("GET", f"/internal/messages/unread-sent/{agent_id}")
        return data.get("messages", [])

    async def mark_messages_read(self, message_ids):
        return await self._request("PATCH", "/internal/messages/mark-read", {"message_ids": message_ids})

    async def wake_subagent(self, agent_id: str, subagent_id: str):
        return await self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/wake", {})

    async def set_subagent_awake(self, agent_id: str, subagent_id: str):
        return await self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/awake", {})

    async def set_subagent_sleeping(self, agent_id: str, subagent_id: str):
        return await self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/sleeping", {})

    async def get_subagent(self, agent_id: str, subagent_id: str):
        return await self._request("GET", f"/internal/subagents/{agent_id}/{subagent_id}")

    async def get_subagent_status(self, agent_id: str, subagent_id: str):
        return await self._request("GET", f"/internal/subagents/{agent_id}/{subagent_id}/status")

    async def create_aggregate_mcp(self, agent_id: str, runtime_id: str, subagent_id: str):
        return await self._request("POST", "/internal/mcp/aggregate", {
            "agent_id": agent_id,
            "runtime_id": runtime_id,
            "subagent_id": subagent_id,
        })

    async def destroy_aggregate_mcp(self, agent_id: str, runtime_id: str):
        return await self._request("DELETE", f"/internal/mcp/aggregate/{agent_id}/{runtime_id}")

    async def set_runtime_summarized(self, runtime_id: str):
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/summarized")

    async def set_runtime_need_rest(self, runtime_id: str, value: bool):
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/need-rest", {"value": value})

    async def set_runtime_status(self, runtime_id: str, expected_status, new_status: str, error: str = None):
        payload = {"expected_status": expected_status, "new_status": new_status}
        if error:
            payload["error"] = error
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/set-status", payload)


@pytest_asyncio.fixture
async def gateway_app(db: Database) -> AsyncGenerator[FastAPI, None]:
    """FastAPI app with internal + task queue routers for HTTP-based tests."""
    db_module._database = db
    app = FastAPI()

    queue = await init_task_queue(db)
    orchestrator = await init_saga_orchestrator(db)

    app.include_router(internal_router, prefix="/internal")
    app.include_router(create_task_queue_router(queue, orchestrator), prefix="/internal/tq")
    app.include_router(create_handler_router(lambda: get_handler_context()), prefix="/internal/tq/handlers")
    app.include_router(create_business_router(orchestrator, lambda: get_handler_context()), prefix="/internal/tq/business")
    app.include_router(create_recovery_router(queue, orchestrator), prefix="/internal/tq/recover")

    gateway_client = TestGatewayClient(app)
    set_handler_context({
        "gateway_url": "http://test",
        "gateway_client": gateway_client,
        "mcp_client": None,
        "llm_client": None,
        "saga_client": None,
    })

    yield app

    await shutdown_task_queue()
    db_module._database = None


@pytest_asyncio.fixture
async def gateway_http_client(gateway_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=gateway_app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_with_agent(db: Database) -> AsyncGenerator[tuple, None]:
    """
    Database with a pre-created test agent and main subagent.
    
    Returns:
        Tuple of (database, agent_id)
    """
    agent_id = "test-agent-001"
    # Note: create_main_runtime uses main-{agent_id[:8]} format
    subagent_id = f"main-{agent_id[:8]}"
    
    # Insert a test agent (using correct schema columns)
    db.execute("""
        INSERT INTO agents (id, name, setup_complete, vm_config, ports, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (agent_id, "Test Agent", 1, "{}", "{}"))
    
    # Insert a main subagent (required by agent_runtimes foreign key)
    db.execute("""
        INSERT INTO subagents (subagent_id, agent_id, type, status, created_at, updated_at)
        VALUES (?, ?, 'main', 'sleeping', datetime('now'), datetime('now'))
    """, (subagent_id, agent_id))
    
    db.commit()
    
    yield db, agent_id


# ==================== Repository Fixtures ====================

@pytest_asyncio.fixture
async def runtime_repo(db: Database):
    """RuntimeRepository fixture."""
    from gateway.db.repositories.runtime import RuntimeRepository
    return RuntimeRepository(db)


@pytest_asyncio.fixture
async def message_repo(db: Database):
    """MessageRepository fixture."""
    from gateway.db.repositories.message import MessageRepository
    return MessageRepository(db)


@pytest_asyncio.fixture
async def agent_state_repo(db: Database):
    """AgentStateRepository fixture."""
    from gateway.db.repositories.agent_state import AgentStateRepository
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
        return runtime_repo.create_main_runtime(agent_id)
    else:
        return runtime_repo.create_sub_runtime(
            agent_id, 
            parent_subagent_id="main-parent"
        )


async def create_test_message(db: Database, agent_id: str, content: str = "Test message"):
    """Helper to create a test message in inbox."""
    from datetime import datetime
    import uuid
    
    msg_id = f"msg-{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    
    db.execute("""
        INSERT INTO chat_messages (id, agent_id, type, content, read, processed, timestamp)
        VALUES (?, ?, ?, ?, 0, 0, ?)
    """, (msg_id, agent_id, "USER_MESSAGE", content, now))
    db.commit()
    
    return msg_id
