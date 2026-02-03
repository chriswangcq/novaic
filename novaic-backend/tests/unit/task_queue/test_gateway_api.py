"""
Gateway task queue API tests (HTTP-based).
"""

import pytest


@pytest.mark.asyncio
async def test_list_handler_topics(gateway_http_client):
    resp = await gateway_http_client.get("/internal/tq/handlers/topics")
    assert resp.status_code == 200
    data = resp.json()
    assert "topics" in data
    assert "subagent.wake" in data["topics"]


@pytest.mark.asyncio
async def test_business_message_process_wake_only(gateway_http_client):
    # Ensure main subagent exists
    resp = await gateway_http_client.get("/internal/subagents/agent-1/main")
    assert resp.status_code == 200

    resp = await gateway_http_client.post("/internal/tq/business/message/process", json={
        "message_id": "msg-1",
        "agent_id": "agent-1",
        "content": "Hello",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["action"] in ("wake_only", "runtime_start", "pending")
