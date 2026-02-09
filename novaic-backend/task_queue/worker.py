"""
Worker - 通用任务执行器

职责：
1. 轮询认领任务
2. 调用业务 Handler
3. 更新任务状态
4. 心跳保活

设计原则：
- 通用化，不包含任何业务逻辑
- 业务逻辑通过 Handler 注入
- 支持多 topic 订阅
"""

import asyncio
import signal
import sys
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Awaitable

from .saga import TaskQueueProtocol
from .exceptions import RetryableError
from common.utils.time import utc_now_iso


# Handler 类型定义
HandlerFunc = Callable[[str, Dict[str, Any]], Awaitable[Any]]


@dataclass
class WorkerMetrics:
    """Worker 性能指标"""
    claimed: int = 0
    processed: int = 0
    failed: int = 0
    retried: int = 0
    total_process_time_ms: float = 0.0
    last_claim_at: Optional[str] = None
    last_process_at: Optional[str] = None
    started_at: Optional[str] = None
    
    @property
    def avg_process_time_ms(self) -> float:
        if self.processed == 0:
            return 0.0
        return self.total_process_time_ms / self.processed
    
    def to_dict(self) -> dict:
        return {
            "claimed": self.claimed,
            "processed": self.processed,
            "failed": self.failed,
            "retried": self.retried,
            "avg_process_time_ms": round(self.avg_process_time_ms, 2),
            "last_claim_at": self.last_claim_at,
            "last_process_at": self.last_process_at,
            "started_at": self.started_at,
        }


class Worker:
    """
    通用任务 Worker
    
    使用方式：
        # 定义 Handler
        async def my_handler(topic: str, payload: dict) -> dict:
            if topic == "send_email":
                send_email(payload["to"], payload["subject"])
                return {"sent": True}
        
        # 创建并运行 Worker
        worker = Worker(
            queue=task_queue,
            topics=["send_email", "send_sms"],
            handler=my_handler,
        )
        await worker.run()
    """
    
    def __init__(
        self,
        queue: TaskQueueProtocol,
        topics: List[str],
        handler: HandlerFunc,
        worker_id: Optional[str] = None,
        poll_interval: float = 0.1,
        heartbeat_interval: float = 10.0,
        name: str = "worker",
    ):
        """
        初始化 Worker
        
        Args:
            queue: TaskQueue 实例
            topics: 订阅的 topic 列表
            handler: 任务处理函数 (topic, payload) -> result
            worker_id: Worker 标识（可选，自动生成）
            poll_interval: 轮询间隔（秒）
            heartbeat_interval: 心跳间隔（秒）
            name: Worker 名称（用于日志）
        """
        self.queue = queue
        self.topics = topics
        self.handler = handler
        self.worker_id = worker_id or f"{name}-{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.name = name
        
        # 运行状态
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._current_task: Optional[dict] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # 指标
        self.metrics = WorkerMetrics()
    
    async def run(self):
        """
        主循环
        
        轮询认领任务，调用 Handler 处理，更新状态。
        支持优雅关闭。
        """
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = utc_now_iso()
        
        # 设置信号处理
        self._setup_signals()
        
        # 启动心跳后台任务
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        self._log(f"Starting (worker_id: {self.worker_id}, topics: {self.topics})...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # 尝试认领任务
                    task = await self.queue.claim(self.topics, self.worker_id)
                    
                    if task:
                        self._current_task = task
                        self.metrics.claimed += 1
                        self.metrics.last_claim_at = utc_now_iso()
                        
                        # 处理任务
                        await self._process_task(task)
                        
                        self._current_task = None
                    else:
                        # 无任务，等待
                        await asyncio.sleep(self.poll_interval)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    await asyncio.sleep(self.poll_interval)
        
        finally:
            self._running = False
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            self._log("Stopped")
    
    async def _process_task(self, task: dict):
        """处理单个任务"""
        task_id = task.get("id")
        topic = task.get("topic")
        payload = task.get("payload", {})
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            self._log(f"Processing task {task_id} (topic: {topic})")
            
            # 调用业务 Handler
            result = await self.handler(topic, payload)
            
            # 计算耗时
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            self.metrics.processed += 1
            self.metrics.total_process_time_ms += elapsed_ms
            self.metrics.last_process_at = utc_now_iso()
            
            # 标记完成
            await self.queue.complete(task_id, result)
            self._log(f"Task {task_id} completed ({elapsed_ms:.1f}ms)")
            
        except RetryableError as e:
            # 可重试错误
            final_status = await self.queue.fail(task_id, str(e), retry=True)
            self.metrics.retried += 1
            self._log(f"Task {task_id} will retry: {e} (status: {final_status})", level="warning")
            
        except Exception as e:
            # 永久失败
            self.metrics.failed += 1
            await self.queue.fail(task_id, str(e), retry=False)
            self._log(f"Task {task_id} failed: {e}", level="error")
            traceback.print_exc()
    
    async def _heartbeat_loop(self):
        """心跳后台任务"""
        while not self._shutdown_event.is_set():
            try:
                if self._current_task:
                    task_id = self._current_task.get("id")
                    await self.queue.heartbeat(task_id)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"Heartbeat error: {e}", level="error")
                await asyncio.sleep(self.heartbeat_interval)
    
    def _setup_signals(self):
        """设置信号处理"""
        if sys.platform == "win32":
            return
        
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
    
    async def shutdown(self):
        """优雅关闭"""
        self._log("Shutdown requested...")
        self._shutdown_event.set()
    
    def _log(self, message: str, level: str = "info"):
        """日志"""
        prefix = f"[{self.name}]"
        if level == "error":
            print(f"{prefix} ERROR: {message}")
        elif level == "warning":
            print(f"{prefix} WARNING: {message}")
        else:
            print(f"{prefix} {message}")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def get_status(self) -> dict:
        """获取 Worker 状态"""
        return {
            "name": self.name,
            "worker_id": self.worker_id,
            "topics": self.topics,
            "running": self._running,
            "has_current_task": self._current_task is not None,
            "current_task_id": self._current_task.get("id") if self._current_task else None,
            "metrics": self.metrics.to_dict(),
        }


class MultiTopicWorker(Worker):
    """
    多 Topic Worker，支持为不同 topic 注册不同的 Handler
    
    使用方式：
        worker = MultiTopicWorker(queue=task_queue)
        
        @worker.register("send_email")
        async def handle_email(payload):
            ...
        
        @worker.register("send_sms")
        async def handle_sms(payload):
            ...
        
        await worker.run()
    """
    
    def __init__(
        self,
        queue: TaskQueueProtocol,
        worker_id: Optional[str] = None,
        poll_interval: float = 0.1,
        heartbeat_interval: float = 10.0,
        name: str = "multi-worker",
    ):
        self._handlers: Dict[str, HandlerFunc] = {}
        
        # 初始化父类，handler 稍后设置
        super().__init__(
            queue=queue,
            topics=[],
            handler=self._dispatch_handler,
            worker_id=worker_id,
            poll_interval=poll_interval,
            heartbeat_interval=heartbeat_interval,
            name=name,
        )
    
    def register(self, topic: str):
        """
        装饰器：注册 topic Handler
        
        Args:
            topic: Topic 名称
        """
        def decorator(func: Callable[[Dict[str, Any]], Awaitable[Any]]):
            async def wrapper(t: str, payload: Dict[str, Any]) -> Any:
                return await func(payload)
            
            self._handlers[topic] = wrapper
            if topic not in self.topics:
                self.topics.append(topic)
            return func
        return decorator
    
    def add_handler(self, topic: str, handler: Callable[[Dict[str, Any]], Awaitable[Any]]):
        """
        编程方式注册 Handler
        
        Args:
            topic: Topic 名称
            handler: 处理函数 (payload) -> result
        """
        async def wrapper(t: str, payload: Dict[str, Any]) -> Any:
            return await handler(payload)
        
        self._handlers[topic] = wrapper
        if topic not in self.topics:
            self.topics.append(topic)
    
    async def _dispatch_handler(self, topic: str, payload: Dict[str, Any]) -> Any:
        """分发到对应的 Handler"""
        handler = self._handlers.get(topic)
        if not handler:
            raise ValueError(f"No handler registered for topic: {topic}")
        return await handler(topic, payload)


async def run_workers(*workers: Worker):
    """
    并发运行多个 Worker
    
    Args:
        workers: Worker 实例列表
        
    Example:
        await run_workers(
            Worker(queue, ["topic_a"], handler_a),
            Worker(queue, ["topic_b"], handler_b),
        )
    """
    tasks = [asyncio.create_task(w.run()) for w in workers]
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for w in workers:
            await w.shutdown()
        await asyncio.gather(*tasks, return_exceptions=True)
