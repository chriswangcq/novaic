"""
Task Queue Routes tests (HTTP-based).
"""

import pytest


@pytest.mark.asyncio
async def test_publish_and_get(gateway_http_client):
    resp = await gateway_http_client.post("/internal/tq/tasks/publish", json={
        "topic": "test_topic",
        "payload": {"key": "value"},
    })
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]

    resp = await gateway_http_client.get(f"/internal/tq/tasks/{task_id}")
    assert resp.status_code == 200
    task = resp.json()["task"]
    assert task["topic"] == "test_topic"
    assert task["status"] == "pending"


@pytest.mark.asyncio
async def test_claim_and_complete(gateway_http_client):
    resp = await gateway_http_client.post("/internal/tq/tasks/publish", json={
        "topic": "test_topic",
        "payload": {},
    })
    task_id = resp.json()["task_id"]

    resp = await gateway_http_client.post("/internal/tq/tasks/claim", json={
        "topics": ["test_topic"],
        "worker_id": "worker-1",
    })
    assert resp.status_code == 200
    task = resp.json()["task"]
    assert task["id"] == task_id
    assert task["status"] == "claimed"

    resp = await gateway_http_client.post(f"/internal/tq/tasks/{task_id}/complete", json={
        "result": {"done": True},
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_claim_no_tasks(gateway_http_client):
    resp = await gateway_http_client.post("/internal/tq/tasks/claim", json={
        "topics": ["nonexistent"],
        "worker_id": "worker-1",
    })
    assert resp.status_code == 200
    assert resp.json()["task"] is None


@pytest.mark.asyncio
async def test_fail_with_retry(gateway_http_client):
    resp = await gateway_http_client.post("/internal/tq/tasks/publish", json={
        "topic": "test_topic",
        "payload": {},
        "max_retries": 3,
    })
    task_id = resp.json()["task_id"]

    await gateway_http_client.post("/internal/tq/tasks/claim", json={
        "topics": ["test_topic"],
        "worker_id": "worker-1",
    })

    resp = await gateway_http_client.post(f"/internal/tq/tasks/{task_id}/fail", json={
        "error": "test error",
        "retry": True,
    })
    assert resp.status_code == 200
    assert resp.json()["final_status"] == "pending"


@pytest.mark.asyncio
async def test_heartbeat(gateway_http_client):
    resp = await gateway_http_client.post("/internal/tq/tasks/publish", json={
        "topic": "test_topic",
        "payload": {},
    })
    task_id = resp.json()["task_id"]

    await gateway_http_client.post("/internal/tq/tasks/claim", json={
        "topics": ["test_topic"],
        "worker_id": "worker-1",
    })

    resp = await gateway_http_client.post(f"/internal/tq/tasks/{task_id}/heartbeat", json={})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
