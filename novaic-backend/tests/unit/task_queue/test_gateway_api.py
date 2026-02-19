"""
Gateway task queue API tests (HTTP-based).
"""

import pytest


@pytest.mark.asyncio
async def test_list_handler_topics(gateway_http_client):
    # Queue topics are discovered from published tasks.
    pub = await gateway_http_client.post("/internal/tq/tasks/publish", json={
        "topic": "message.route",
        "payload": {"message_id": "msg-seed", "agent_id": "agent-1"},
    })
    assert pub.status_code == 200

    resp = await gateway_http_client.get("/internal/tq/topics")
    assert resp.status_code == 200
    data = resp.json()
    assert "topics" in data
    assert "message.route" in data["topics"]


@pytest.mark.asyncio
async def test_message_route_task_can_be_published(gateway_http_client):
    """Business entry is async via queue topic publish."""
    resp = await gateway_http_client.post("/internal/tq/tasks/publish", json={
        "topic": "message.route",
        "payload": {
            "message_id": "msg-1",
            "agent_id": "agent-1",
            "content": "Hello",
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data and data["task_id"]
