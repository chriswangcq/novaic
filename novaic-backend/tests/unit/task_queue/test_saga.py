"""
Saga API tests (HTTP-based).
"""

import pytest


@pytest.mark.asyncio
async def test_saga_start_and_get(gateway_http_client):
    resp = await gateway_http_client.post("/internal/tq/sagas/start", json={
        "saga_type": "test_saga",
        "context": {"foo": "bar"},
        "idempotency_key": "test-saga-key-1",
    })
    assert resp.status_code == 200
    saga_id = resp.json()["saga_id"]

    get_resp = await gateway_http_client.get(f"/internal/tq/sagas/{saga_id}")
    assert get_resp.status_code == 200
    saga = get_resp.json()["saga"]
    assert saga["id"] == saga_id
    assert saga["status"] == "pending"


@pytest.mark.asyncio
async def test_saga_idempotency(gateway_http_client):
    resp1 = await gateway_http_client.post("/internal/tq/sagas/start", json={
        "saga_type": "test_saga",
        "context": {"value": 1},
        "idempotency_key": "test-saga-key-2",
    })
    resp2 = await gateway_http_client.post("/internal/tq/sagas/start", json={
        "saga_type": "test_saga",
        "context": {"value": 2},
        "idempotency_key": "test-saga-key-2",
    })
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["saga_id"] == resp2.json()["saga_id"]


@pytest.mark.asyncio
async def test_saga_claim_progress_complete(gateway_http_client):
    start_resp = await gateway_http_client.post("/internal/tq/sagas/start", json={
        "saga_type": "test_saga",
        "context": {"value": 3},
    })
    saga_id = start_resp.json()["saga_id"]

    claim_resp = await gateway_http_client.post("/internal/tq/sagas/claim", json={
        "saga_types": ["test_saga"],
        "worker_id": "worker-1",
    })
    assert claim_resp.status_code == 200
    assert claim_resp.json().get("saga") is not None

    progress_resp = await gateway_http_client.post(f"/internal/tq/sagas/{saga_id}/progress", json={
        "current_step": 1,
        "step_results": {"step1": {"success": True}},
        "status": "running",
    })
    assert progress_resp.status_code == 200

    complete_resp = await gateway_http_client.post(f"/internal/tq/sagas/{saga_id}/complete", json={
        "step_results": {"step1": {"success": True}},
    })
    assert complete_resp.status_code == 200

    saga_resp = await gateway_http_client.get(f"/internal/tq/sagas/{saga_id}")
    assert saga_resp.json()["saga"]["status"] == "completed"


@pytest.mark.asyncio
async def test_saga_fail(gateway_http_client):
    start_resp = await gateway_http_client.post("/internal/tq/sagas/start", json={
        "saga_type": "test_saga",
        "context": {"value": 4},
    })
    saga_id = start_resp.json()["saga_id"]

    fail_resp = await gateway_http_client.post(f"/internal/tq/sagas/{saga_id}/fail", json={
        "error": "boom",
    })
    assert fail_resp.status_code == 200

    saga_resp = await gateway_http_client.get(f"/internal/tq/sagas/{saga_id}")
    assert saga_resp.json()["saga"]["status"] == "failed"
