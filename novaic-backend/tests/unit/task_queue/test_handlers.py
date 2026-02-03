"""
Task Handlers tests (HTTP-based).
"""

import pytest

from task_queue.handlers import get_all_topics, get_handler


def test_get_all_topics():
    topics = get_all_topics()
    assert len(topics) > 0
    assert "subagent.wake" in topics
    assert "runtime.create" in topics


def test_get_handler_not_found():
    with pytest.raises(ValueError, match="No handler"):
        get_handler("nonexistent.topic")


@pytest.mark.asyncio
async def test_execute_subagent_wake(gateway_http_client):
    # Ensure main subagent exists
    resp = await gateway_http_client.get("/internal/subagents/agent-1/main")
    assert resp.status_code == 200
    subagent_id = resp.json()["subagent_id"]

    # Execute handler
    resp = await gateway_http_client.post("/internal/tq/handlers/execute", json={
        "topic": "subagent.wake",
        "payload": {
            "agent_id": "agent-1",
            "subagent_id": subagent_id,
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["result"]["new_status"] in ("awaking", "awake")
