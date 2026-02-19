from unittest.mock import Mock

from common.exceptions import BusinessError
from task_queue.retry_policy import RetryPolicy
from task_queue.workers.task_worker_sync import TaskWorkerSync


def test_retry_policy_classifies_business_error_as_non_retryable():
    policy = RetryPolicy(max_attempts=3, backoff_base=0.1, backoff_max=1.0)

    decision = policy.evaluate(BusinessError("bad request"), attempt=1)

    assert decision.retry is False
    assert decision.reason == "business_error"
    assert decision.backoff_seconds == 0.0


def test_retry_policy_applies_exponential_backoff_and_max_attempts():
    policy = RetryPolicy(max_attempts=3, backoff_base=0.5, backoff_max=2.0)

    d1 = policy.evaluate(TimeoutError("timeout"), attempt=1)
    d2 = policy.evaluate(TimeoutError("timeout"), attempt=2)
    d3 = policy.evaluate(TimeoutError("timeout"), attempt=3)

    assert d1.retry is True
    assert d1.backoff_seconds == 0.5

    assert d2.retry is True
    assert d2.backoff_seconds == 1.0

    assert d3.retry is False
    assert d3.reason == "max_attempts_exhausted"


def test_task_worker_uses_inprocess_idempotency_guard_for_duplicates():
    worker = TaskWorkerSync(
        topics=["topic.test"],
        queue_service_url="http://queue.local",
        gateway_url="http://gateway.local",
    )

    worker.client = Mock()
    worker.client.acquire_idempotency_execution = Mock(return_value={"action": "acquired"})
    worker.client.complete_idempotency_execution = Mock(return_value=True)
    worker.client.release_idempotency_execution = Mock(return_value=True)
    worker.saga_client = Mock()
    worker.gateway_client = Mock()
    worker.ro_client = Mock()
    worker._call_handler = Mock(return_value={"ok": True})

    first_task = {
        "id": "task-1",
        "topic": "topic.test",
        "idempotency_key": "idem-1",
        "retry_count": 0,
        "max_retries": 3,
        "payload": {},
    }
    duplicate_task = {
        "id": "task-2",
        "topic": "topic.test",
        "idempotency_key": "idem-1",
        "retry_count": 0,
        "max_retries": 3,
        "payload": {},
    }

    worker._execute_task(first_task)
    worker.client.acquire_idempotency_execution.return_value = {
        "action": "completed",
        "result": {"ok": True},
    }
    worker._execute_task(duplicate_task)

    assert worker._call_handler.call_count == 1
    assert worker.client.complete.call_count == 2
    assert worker.metrics.tasks_succeeded == 2
