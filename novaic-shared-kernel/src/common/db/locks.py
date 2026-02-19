"""Database lock management."""

import threading
import time
from collections import deque
from contextlib import contextmanager
from typing import Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class LockStrategy(ABC):
    @abstractmethod
    @contextmanager
    def acquire(self, **kwargs):
        pass


class FIFOLock(LockStrategy):
    def __init__(self):
        self._lock = threading.Lock()
        self._queue = deque()
        self._metrics = {"total_acquires": 0, "current_waiting": 0, "max_waiting": 0}

    @contextmanager
    def acquire(self, **kwargs):
        resource_id = kwargs.get("resource_id", "unknown")
        timeout = kwargs.get("timeout")
        event = threading.Event()
        start_time = time.time()

        with self._lock:
            self._queue.append(event)
            self._metrics["total_acquires"] += 1
            self._metrics["current_waiting"] = len(self._queue)
            self._metrics["max_waiting"] = max(self._metrics["max_waiting"], self._metrics["current_waiting"])
            if len(self._queue) == 1:
                event.set()

        if timeout:
            acquired = event.wait(timeout=timeout)
            if not acquired:
                with self._lock:
                    try:
                        self._queue.remove(event)
                        self._metrics["current_waiting"] = len(self._queue)
                    except ValueError:
                        pass
                raise TimeoutError(f"Failed to acquire lock for {resource_id} after {time.time() - start_time:.2f}s")
        else:
            event.wait()

        try:
            yield
        finally:
            with self._lock:
                try:
                    self._queue.popleft()
                    self._metrics["current_waiting"] = len(self._queue)
                    if self._queue:
                        self._queue[0].set()
                except IndexError:
                    pass

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return self._metrics.copy()


class ShardedFIFOLock(LockStrategy):
    def __init__(self, num_shards: int = 8):
        self.num_shards = num_shards
        self.shards = [FIFOLock() for _ in range(num_shards)]

    def _get_shard(self, resource_id: str) -> FIFOLock:
        return self.shards[hash(resource_id) % self.num_shards]

    @contextmanager
    def acquire(self, **kwargs):
        resource_id = kwargs.get("resource_id")
        if not resource_id:
            raise ValueError("resource_id is required for ShardedFIFOLock")
        with self._get_shard(resource_id).acquire(**kwargs):
            yield

    def get_metrics(self) -> Dict[str, Any]:
        total_acquires = 0
        current_waiting = 0
        max_waiting = 0
        for shard in self.shards:
            metrics = shard.get_metrics()
            total_acquires += metrics["total_acquires"]
            current_waiting += metrics["current_waiting"]
            max_waiting = max(max_waiting, metrics["max_waiting"])
        return {
            "total_acquires": total_acquires,
            "current_waiting": current_waiting,
            "max_waiting": max_waiting,
            "num_shards": self.num_shards,
        }


class DatabaseLockManager:
    def __init__(self):
        self.global_lock = FIFOLock()
        self.message_locks = ShardedFIFOLock(num_shards=8)
        self.agent_locks = ShardedFIFOLock(num_shards=4)
        self.task_locks = ShardedFIFOLock(num_shards=8)
        self.saga_locks = ShardedFIFOLock(num_shards=8)
        self._lock_map = {
            "global": self.global_lock,
            "message": self.message_locks,
            "agent": self.agent_locks,
            "task": self.task_locks,
            "saga": self.saga_locks,
        }

    @contextmanager
    def acquire(self, lock_type: str, **kwargs):
        lock = self._lock_map.get(lock_type)
        if not lock:
            raise ValueError(f"Invalid lock_type: {lock_type}. Valid types: {list(self._lock_map.keys())}")
        with lock.acquire(**kwargs):
            yield
