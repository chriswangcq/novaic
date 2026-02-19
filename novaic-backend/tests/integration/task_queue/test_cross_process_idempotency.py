"""
Integration tests for cross-process/restart idempotency guard behavior.
"""

import asyncio
import time

import pytest


async def _publish_and_claim(client, idempotency_key: str):
    pub = await client.post(
        "/internal/tq/tasks/publish",
        json={
            "topic": "cross_process_topic",
            "payload": {"x": 1},
            "idempotency_key": idempotency_key,
            "max_retries": 3,
        },
    )
    assert pub.status_code == 200
    task_id = pub.json()["task_id"]

    claim = await client.post(
        "/internal/tq/tasks/claim",
        json={"topics": ["cross_process_topic"], "worker_id": "worker-a"},
    )
    assert claim.status_code == 200
    task = claim.json()["task"]
    assert task is not None
    assert task["id"] == task_id
    return task_id


@pytest.mark.asyncio
async def test_cross_process_idempotency_contention_and_completed_short_circuit(gateway_http_client):
    task_id = await _publish_and_claim(gateway_http_client, "idem-cross-1")

    acquire_1 = await gateway_http_client.post(
        f"/internal/tq/tasks/{task_id}/idempotency/acquire",
        json={"idempotency_key": "idem-cross-1", "owner_token": "worker-a:token-1", "lease_seconds": 3},
    )
    assert acquire_1.status_code == 200
    assert acquire_1.json()["action"] == "acquired"

    acquire_2 = await gateway_http_client.post(
        f"/internal/tq/tasks/{task_id}/idempotency/acquire",
        json={"idempotency_key": "idem-cross-1", "owner_token": "worker-b:token-2", "lease_seconds": 3},
    )
    assert acquire_2.status_code == 200
    assert acquire_2.json()["action"] == "in_progress"

    complete_guard = await gateway_http_client.post(
        f"/internal/tq/tasks/{task_id}/idempotency/complete",
        json={
            "idempotency_key": "idem-cross-1",
            "owner_token": "worker-a:token-1",
            "result": {"ok": True, "source": "first-exec"},
        },
    )
    assert complete_guard.status_code == 200
    assert complete_guard.json()["success"] is True

    acquire_3 = await gateway_http_client.post(
        f"/internal/tq/tasks/{task_id}/idempotency/acquire",
        json={"idempotency_key": "idem-cross-1", "owner_token": "worker-c:token-3", "lease_seconds": 3},
    )
    assert acquire_3.status_code == 200
    assert acquire_3.json()["action"] == "completed"
    assert acquire_3.json()["result"]["source"] == "first-exec"


@pytest.mark.asyncio
async def test_restart_takeover_after_lease_expiry(gateway_http_client):
    task_id = await _publish_and_claim(gateway_http_client, "idem-restart-1")

    acquire_old = await gateway_http_client.post(
        f"/internal/tq/tasks/{task_id}/idempotency/acquire",
        json={"idempotency_key": "idem-restart-1", "owner_token": "old-worker:token-1", "lease_seconds": 1},
    )
    assert acquire_old.status_code == 200
    assert acquire_old.json()["action"] == "acquired"

    await asyncio.sleep(1.1)

    acquire_new = await gateway_http_client.post(
        f"/internal/tq/tasks/{task_id}/idempotency/acquire",
        json={"idempotency_key": "idem-restart-1", "owner_token": "new-worker:token-2", "lease_seconds": 2},
    )
    assert acquire_new.status_code == 200
    assert acquire_new.json()["action"] == "acquired"


@pytest.mark.asyncio
async def test_high_concurrency_duplicate_task_stress_variant(gateway_http_client):
    task_id = await _publish_and_claim(gateway_http_client, "idem-stress-1")

    async def acquire_once(idx: int):
        resp = await gateway_http_client.post(
            f"/internal/tq/tasks/{task_id}/idempotency/acquire",
            json={
                "idempotency_key": "idem-stress-1",
                "owner_token": f"worker-{idx}:token-{idx}",
                "lease_seconds": 5,
            },
        )
        assert resp.status_code == 200
        return idx, resp.json()["action"]

    attempts = await asyncio.gather(*[acquire_once(i) for i in range(12)])
    acquired = [item for item in attempts if item[1] == "acquired"]
    in_progress = [item for item in attempts if item[1] == "in_progress"]

    assert len(acquired) == 1
    assert len(in_progress) == 11

    winner_idx = acquired[0][0]
    done_resp = await gateway_http_client.post(
        f"/internal/tq/tasks/{task_id}/idempotency/complete",
        json={
            "idempotency_key": "idem-stress-1",
            "owner_token": f"worker-{winner_idx}:token-{winner_idx}",
            "result": {"ok": True, "winner": winner_idx},
        },
    )
    assert done_resp.status_code == 200
    assert done_resp.json()["success"] is True

    follow_up = await gateway_http_client.post(
        f"/internal/tq/tasks/{task_id}/idempotency/acquire",
        json={
            "idempotency_key": "idem-stress-1",
            "owner_token": "worker-final:token-final",
            "lease_seconds": 5,
        },
    )
    assert follow_up.status_code == 200
    assert follow_up.json()["action"] == "completed"
    assert follow_up.json()["result"]["winner"] == winner_idx


@pytest.mark.asyncio
async def test_high_load_replay_throughput_and_exactly_once(gateway_http_client):
    task_id = await _publish_and_claim(gateway_http_client, "idem-highload-1")
    concurrency = 80
    start = time.perf_counter()

    async def acquire_once(idx: int):
        resp = await gateway_http_client.post(
            f"/internal/tq/tasks/{task_id}/idempotency/acquire",
            json={
                "idempotency_key": "idem-highload-1",
                "owner_token": f"hl-worker-{idx}:token-{idx}",
                "lease_seconds": 4,
            },
        )
        assert resp.status_code == 200
        return idx, resp.json()["action"]

    attempts = await asyncio.gather(*[acquire_once(i) for i in range(concurrency)])
    elapsed = max(0.001, time.perf_counter() - start)
    throughput = concurrency / elapsed

    acquired = [item for item in attempts if item[1] == "acquired"]
    in_progress = [item for item in attempts if item[1] == "in_progress"]

    assert len(acquired) == 1
    assert len(in_progress) == concurrency - 1

    winner_idx = acquired[0][0]
    done_resp = await gateway_http_client.post(
        f"/internal/tq/tasks/{task_id}/idempotency/complete",
        json={
            "idempotency_key": "idem-highload-1",
            "owner_token": f"hl-worker-{winner_idx}:token-{winner_idx}",
            "result": {"ok": True, "winner": winner_idx, "concurrency": concurrency},
        },
    )
    assert done_resp.status_code == 200
    assert done_resp.json()["success"] is True

    diag_resp = await gateway_http_client.get("/internal/tq/tasks/idempotency/diagnostics?limit=5&only_contended=true")
    assert diag_resp.status_code == 200
    rows = diag_resp.json()["diagnostics"]
    target = [row for row in rows if row["idempotency_key"] == "idem-highload-1"]
    assert target, "expected idem-highload-1 in diagnostics output"
    assert target[0]["contention_count"] >= concurrency - 1

    print(
        "HIGH_LOAD_REPLAY_METRICS "
        f"concurrency={concurrency} elapsed_sec={elapsed:.3f} "
        f"throughput_ops_per_sec={throughput:.2f} exactly_once_winner={winner_idx}"
    )
