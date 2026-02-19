"""
TaskQueue 单元测试
"""

import pytest
import asyncio


async def publish_task(client, topic, payload, idempotency_key=None, max_retries=3):
    resp = await client.post("/internal/tq/tasks/publish", json={
        "topic": topic,
        "payload": payload,
        "idempotency_key": idempotency_key,
        "max_retries": max_retries,
    })
    assert resp.status_code == 200
    return resp.json()["task_id"]


async def claim_task(client, topics, worker_id):
    resp = await client.post("/internal/tq/tasks/claim", json={
        "topics": topics,
        "worker_id": worker_id,
    })
    assert resp.status_code == 200
    return resp.json().get("task")


async def get_task(client, task_id):
    resp = await client.get(f"/internal/tq/tasks/{task_id}")
    if resp.status_code == 404:
        return None
    assert resp.status_code == 200
    return resp.json().get("task")


async def complete_task(client, task_id, result=None):
    resp = await client.post(f"/internal/tq/tasks/{task_id}/complete", json={"result": result})
    assert resp.status_code == 200
    return resp.json().get("success", False)


async def fail_task(client, task_id, error, retry=True, retry_delay_seconds=None):
    resp = await client.post(f"/internal/tq/tasks/{task_id}/fail", json={
        "error": error,
        "retry": retry,
        "retry_delay_seconds": retry_delay_seconds,
    })
    assert resp.status_code == 200
    return resp.json().get("final_status")


async def heartbeat_task(client, task_id):
    resp = await client.post(f"/internal/tq/tasks/{task_id}/heartbeat", json={})
    assert resp.status_code == 200
    return resp.json().get("success", False)


class TestPublish:
    """publish() 测试"""
    
    @pytest.mark.asyncio
    async def test_publish_basic(self, gateway_http_client):
        """基本发布"""
        task_id = await publish_task(
            gateway_http_client,
            topic="test_topic",
            payload={"key": "value"},
        )
        
        assert task_id.startswith("task-")
        
        task = await get_task(gateway_http_client, task_id)
        assert task is not None
        assert task["topic"] == "test_topic"
        assert task["status"] == "pending"
        assert task["payload"]["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_publish_with_idempotency_key(self, gateway_http_client):
        """幂等发布"""
        task_id1 = await publish_task(
            gateway_http_client,
            topic="test_topic",
            payload={"key": "value1"},
            idempotency_key="unique-key-1",
        )
        
        # 相同 idempotency_key 应返回相同 task_id
        task_id2 = await publish_task(
            gateway_http_client,
            topic="test_topic",
            payload={"key": "value2"},
            idempotency_key="unique-key-1",
        )
        
        assert task_id1 == task_id2
    
    @pytest.mark.asyncio
    async def test_publish_different_idempotency_keys(self, gateway_http_client):
        """不同幂等键"""
        task_id1 = await publish_task(
            gateway_http_client,
            topic="test_topic",
            payload={"key": "value"},
            idempotency_key="key-1",
        )
        
        task_id2 = await publish_task(
            gateway_http_client,
            topic="test_topic",
            payload={"key": "value"},
            idempotency_key="key-2",
        )
        
        assert task_id1 != task_id2


class TestClaim:
    """claim() 测试"""
    
    @pytest.mark.asyncio
    async def test_claim_basic(self, gateway_http_client):
        """基本认领"""
        # 发布任务
        task_id = await publish_task(gateway_http_client, "test_topic", {"key": "value"})
        
        # 认领
        task = await claim_task(gateway_http_client, ["test_topic"], "worker-1")
        
        assert task is not None
        assert task["id"] == task_id
        assert task["status"] == "claimed"
        assert task["claimed_by"] == "worker-1"
        assert task["payload"]["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_claim_no_tasks(self, gateway_http_client):
        """无任务可认领"""
        task = await claim_task(gateway_http_client, ["test_topic"], "worker-1")
        assert task is None
    
    @pytest.mark.asyncio
    async def test_claim_wrong_topic(self, gateway_http_client):
        """错误 topic"""
        await publish_task(gateway_http_client, "topic_a", {"key": "value"})
        
        task = await claim_task(gateway_http_client, ["topic_b"], "worker-1")
        assert task is None
    
    @pytest.mark.asyncio
    async def test_claim_multiple_topics(self, gateway_http_client):
        """多 topic 认领"""
        await publish_task(gateway_http_client, "topic_a", {"from": "a"})
        await publish_task(gateway_http_client, "topic_b", {"from": "b"})
        
        # 同时监听多个 topic
        task1 = await claim_task(gateway_http_client, ["topic_a", "topic_b"], "worker-1")
        task2 = await claim_task(gateway_http_client, ["topic_a", "topic_b"], "worker-1")
        
        assert task1 is not None
        assert task2 is not None
        assert task1["id"] != task2["id"]
    
    @pytest.mark.asyncio
    async def test_claim_already_claimed(self, gateway_http_client):
        """已认领的任务不能再次认领"""
        await publish_task(gateway_http_client, "test_topic", {"key": "value"})
        
        # 第一次认领
        task1 = await claim_task(gateway_http_client, ["test_topic"], "worker-1")
        assert task1 is not None
        
        # 第二次认领应该失败
        task2 = await claim_task(gateway_http_client, ["test_topic"], "worker-2")
        assert task2 is None


class TestComplete:
    """complete() 测试"""
    
    @pytest.mark.asyncio
    async def test_complete_basic(self, gateway_http_client):
        """基本完成"""
        task_id = await publish_task(gateway_http_client, "test_topic", {"key": "value"})
        await claim_task(gateway_http_client, ["test_topic"], "worker-1")
        
        result = await complete_task(gateway_http_client, task_id, {"result": "ok"})
        
        assert result is True
        
        task = await get_task(gateway_http_client, task_id)
        assert task["status"] == "done"
        assert task["result"]["result"] == "ok"
        assert task["finished_at"] is not None
    
    @pytest.mark.asyncio
    async def test_complete_unclaimed_task(self, gateway_http_client):
        """未认领任务不能完成"""
        task_id = await publish_task(gateway_http_client, "test_topic", {"key": "value"})
        
        result = await complete_task(gateway_http_client, task_id, {"result": "ok"})
        
        assert result is False


class TestFail:
    """fail() 测试"""
    
    @pytest.mark.asyncio
    async def test_fail_with_retry(self, gateway_http_client):
        """失败重试"""
        task_id = await publish_task(gateway_http_client, "test_topic", {"key": "value"}, max_retries=3)
        await claim_task(gateway_http_client, ["test_topic"], "worker-1")
        
        final_status = await fail_task(
            gateway_http_client,
            task_id,
            "some error",
            retry=True,
            retry_delay_seconds=1.0,
        )
        
        assert final_status == "pending"
        
        task = await get_task(gateway_http_client, task_id)
        assert task["status"] == "pending"
        assert task["retry_count"] == 1
        assert task["claimed_by"] is None
        assert task["next_retry_at"] is not None

        # next_retry_at 生效前不可再次 claim
        task_early = await claim_task(gateway_http_client, ["test_topic"], "worker-2")
        assert task_early is None

        await asyncio.sleep(1.1)
        task_late = await claim_task(gateway_http_client, ["test_topic"], "worker-2")
        assert task_late is not None
        assert task_late["id"] == task_id
    
    @pytest.mark.asyncio
    async def test_fail_max_retries_exceeded(self, gateway_http_client):
        """超过最大重试次数"""
        task_id = await publish_task(gateway_http_client, "test_topic", {"key": "value"}, max_retries=1)
        
        # 第一次执行失败
        await claim_task(gateway_http_client, ["test_topic"], "worker-1")
        await fail_task(gateway_http_client, task_id, "error 1", retry=True)
        
        # 第二次执行失败
        await claim_task(gateway_http_client, ["test_topic"], "worker-2")
        final_status = await fail_task(gateway_http_client, task_id, "error 2", retry=True)
        
        assert final_status == "failed"
        
        task = await get_task(gateway_http_client, task_id)
        assert task["status"] == "failed"
        assert task["retry_count"] == 2
    
    @pytest.mark.asyncio
    async def test_fail_no_retry(self, gateway_http_client):
        """永久失败"""
        task_id = await publish_task(gateway_http_client, "test_topic", {"key": "value"})
        await claim_task(gateway_http_client, ["test_topic"], "worker-1")
        
        final_status = await fail_task(gateway_http_client, task_id, "fatal error", retry=False)
        
        assert final_status == "failed"
        
        task = await get_task(gateway_http_client, task_id)
        assert task["status"] == "failed"


class TestHeartbeat:
    """heartbeat() 测试"""
    
    @pytest.mark.asyncio
    async def test_heartbeat_basic(self, gateway_http_client):
        """基本心跳"""
        task_id = await publish_task(gateway_http_client, "test_topic", {"key": "value"})
        await claim_task(gateway_http_client, ["test_topic"], "worker-1")
        
        # 等待一小段时间
        await asyncio.sleep(0.1)
        
        result = await heartbeat_task(gateway_http_client, task_id)
        
        assert result is True
        task = await get_task(gateway_http_client, task_id)
        assert task["heartbeat_at"] is not None
    
    @pytest.mark.asyncio
    async def test_heartbeat_unclaimed_task(self, gateway_http_client):
        """未认领任务心跳失败"""
        task_id = await publish_task(gateway_http_client, "test_topic", {"key": "value"})
        
        result = await heartbeat_task(gateway_http_client, task_id)
        
        assert result is False


class TestRecoverStale:
    """recover_stale() 测试"""
    
    @pytest.mark.asyncio
    async def test_recover_stale_basic(self, gateway_http_client):
        """基本超时恢复"""
        task_id = await publish_task(gateway_http_client, "test_topic", {"key": "value"})
        await claim_task(gateway_http_client, ["test_topic"], "worker-1")

        await asyncio.sleep(1)

        resp = await gateway_http_client.post("/internal/tq/recover/tasks?timeout_seconds=0")
        assert resp.status_code == 200
        recovered = resp.json().get("tasks_recovered", 0)
        
        assert recovered == 1
        
        task = await get_task(gateway_http_client, task_id)
        assert task["status"] == "pending"
        assert task["claimed_by"] is None


class TestConcurrency:
    """并发测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_claim(self, gateway_http_client):
        """并发认领只有一个成功"""
        await publish_task(gateway_http_client, "test_topic", {"key": "value"})
        
        # 并发认领
        results = await asyncio.gather(
            claim_task(gateway_http_client, ["test_topic"], "worker-1"),
            claim_task(gateway_http_client, ["test_topic"], "worker-2"),
            claim_task(gateway_http_client, ["test_topic"], "worker-3"),
        )
        
        # 只有一个成功
        successful = [r for r in results if r is not None]
        assert len(successful) == 1
