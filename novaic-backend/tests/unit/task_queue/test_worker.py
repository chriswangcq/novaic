"""
Worker 单元测试
"""

import pytest
import asyncio
from task_queue.worker import Worker, MultiTopicWorker
from task_queue.exceptions import RetryableError


class HttpTaskQueueAdapter:
    """HTTP-backed TaskQueue adapter for Worker tests."""

    def __init__(self, client):
        self.client = client

    async def publish(self, topic, payload, idempotency_key=None, max_retries=3):
        resp = await self.client.post("/internal/tq/tasks/publish", json={
            "topic": topic,
            "payload": payload,
            "idempotency_key": idempotency_key,
            "max_retries": max_retries,
        })
        resp.raise_for_status()
        return resp.json()["task_id"]

    async def claim(self, topics, worker_id):
        resp = await self.client.post("/internal/tq/tasks/claim", json={
            "topics": topics,
            "worker_id": worker_id,
        })
        resp.raise_for_status()
        return resp.json().get("task")

    async def complete(self, task_id, result=None):
        resp = await self.client.post(f"/internal/tq/tasks/{task_id}/complete", json={"result": result})
        resp.raise_for_status()
        return resp.json().get("success", False)

    async def fail(self, task_id, error, retry=True):
        resp = await self.client.post(f"/internal/tq/tasks/{task_id}/fail", json={"error": error, "retry": retry})
        resp.raise_for_status()
        return resp.json().get("final_status")

    async def heartbeat(self, task_id):
        resp = await self.client.post(f"/internal/tq/tasks/{task_id}/heartbeat", json={})
        resp.raise_for_status()
        return resp.json().get("success", False)

    async def get_task(self, task_id):
        resp = await self.client.get(f"/internal/tq/tasks/{task_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("task")


class TestWorker:
    """Worker 基本测试"""
    
    @pytest.mark.asyncio
    async def test_worker_process_task(self, gateway_http_client):
        """Worker 处理任务"""
        queue = HttpTaskQueueAdapter(gateway_http_client)
        # 发布任务
        task_id = await queue.publish("test_topic", {"value": 42})
        
        # 记录处理结果
        processed = []
        
        async def handler(topic: str, payload: dict) -> dict:
            processed.append({"topic": topic, "payload": payload})
            return {"processed": True, "doubled": payload["value"] * 2}
        
        # 创建 Worker
        worker = Worker(
            queue=queue,
            topics=["test_topic"],
            handler=handler,
            poll_interval=0.01,
        )
        
        # 运行一段时间
        async def run_briefly():
            task = asyncio.create_task(worker.run())
            await asyncio.sleep(0.2)
            await worker.shutdown()
            await task
        
        await run_briefly()
        
        # 验证处理
        assert len(processed) == 1
        assert processed[0]["topic"] == "test_topic"
        assert processed[0]["payload"]["value"] == 42
        
        # 验证任务状态
        task = await queue.get_task(task_id)
        assert task["status"] == "done"
        assert task["result"]["doubled"] == 84
    
    @pytest.mark.asyncio
    async def test_worker_retryable_error(self, gateway_http_client):
        """Worker 处理可重试错误"""
        queue = HttpTaskQueueAdapter(gateway_http_client)
        task_id = await queue.publish("test_topic", {"value": 1}, max_retries=3)
        
        call_count = 0
        
        async def handler(topic: str, payload: dict) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("Temporary error")
            return {"success": True}
        
        worker = Worker(
            queue=queue,
            topics=["test_topic"],
            handler=handler,
            poll_interval=0.01,
        )
        
        async def run_briefly():
            task = asyncio.create_task(worker.run())
            await asyncio.sleep(0.3)
            await worker.shutdown()
            await task
        
        await run_briefly()
        
        # 验证重试
        assert call_count >= 2
        assert worker.metrics.retried >= 1
        
        # 最终应该成功
        task = await queue.get_task(task_id)
        assert task["status"] == "done"
    
    @pytest.mark.asyncio
    async def test_worker_permanent_failure(self, gateway_http_client):
        """Worker 处理永久失败"""
        queue = HttpTaskQueueAdapter(gateway_http_client)
        task_id = await queue.publish("test_topic", {"value": 1})
        
        async def handler(topic: str, payload: dict) -> dict:
            raise ValueError("Fatal error")
        
        worker = Worker(
            queue=queue,
            topics=["test_topic"],
            handler=handler,
            poll_interval=0.01,
        )
        
        async def run_briefly():
            task = asyncio.create_task(worker.run())
            await asyncio.sleep(0.2)
            await worker.shutdown()
            await task
        
        await run_briefly()
        
        # 验证失败
        task = await queue.get_task(task_id)
        assert task["status"] == "failed"
        assert "Fatal error" in task["error"]
        assert worker.metrics.failed == 1
    
    @pytest.mark.asyncio
    async def test_worker_metrics(self, gateway_http_client):
        """Worker 指标统计"""
        queue = HttpTaskQueueAdapter(gateway_http_client)
        await queue.publish("test_topic", {"id": 1})
        await queue.publish("test_topic", {"id": 2})
        await queue.publish("test_topic", {"id": 3})
        
        async def handler(topic: str, payload: dict) -> dict:
            return {"ok": True}
        
        worker = Worker(
            queue=queue,
            topics=["test_topic"],
            handler=handler,
            poll_interval=0.01,
        )
        
        async def run_briefly():
            task = asyncio.create_task(worker.run())
            await asyncio.sleep(0.3)
            await worker.shutdown()
            await task
        
        await run_briefly()
        
        assert worker.metrics.claimed == 3
        assert worker.metrics.processed == 3
        assert worker.metrics.failed == 0
        assert worker.metrics.avg_process_time_ms > 0


class TestMultiTopicWorker:
    """MultiTopicWorker 测试"""
    
    @pytest.mark.asyncio
    async def test_multi_topic_dispatch(self, gateway_http_client):
        """多 topic 分发"""
        queue = HttpTaskQueueAdapter(gateway_http_client)
        await queue.publish("email", {"to": "test@example.com"})
        await queue.publish("sms", {"phone": "1234567890"})
        
        results = []
        
        worker = MultiTopicWorker(queue=queue, poll_interval=0.01)
        
        @worker.register("email")
        async def handle_email(payload):
            results.append(("email", payload))
            return {"sent": "email"}
        
        @worker.register("sms")
        async def handle_sms(payload):
            results.append(("sms", payload))
            return {"sent": "sms"}
        
        async def run_briefly():
            task = asyncio.create_task(worker.run())
            await asyncio.sleep(0.3)
            await worker.shutdown()
            await task
        
        await run_briefly()
        
        # 验证两种类型都处理了
        topics_processed = [r[0] for r in results]
        assert "email" in topics_processed
        assert "sms" in topics_processed
    
    @pytest.mark.asyncio
    async def test_multi_topic_add_handler(self, gateway_http_client):
        """编程方式添加 handler"""
        queue = HttpTaskQueueAdapter(gateway_http_client)
        await queue.publish("webhook", {"url": "http://example.com"})
        
        processed = []
        
        async def webhook_handler(payload):
            processed.append(payload)
            return {"called": True}
        
        worker = MultiTopicWorker(queue=queue, poll_interval=0.01)
        worker.add_handler("webhook", webhook_handler)
        
        async def run_briefly():
            task = asyncio.create_task(worker.run())
            await asyncio.sleep(0.2)
            await worker.shutdown()
            await task
        
        await run_briefly()
        
        assert len(processed) == 1
        assert processed[0]["url"] == "http://example.com"
