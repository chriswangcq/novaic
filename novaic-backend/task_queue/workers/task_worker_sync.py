"""
同步 TaskWorker - 基于多进程 + 同步代码

特点：
- 纯同步代码（无 async/await）
- 使用现有的 TaskQueueClient（同步 SDK）
- 心跳通过后台线程自动管理
- 多进程并发（绕过 GIL）

对比异步版本：
- 代码更简单（无 asyncio 复杂性）
- 更易调试（同步执行流程）
- 更稳定（进程隔离）
- 性能更好（多核 CPU）
"""

import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback

from task_queue.client import TaskQueueClient, GatewayInternalClient, SagaClient
from task_queue.heartbeat_sync import HeartbeatSync
from task_queue.exceptions import RETRYABLE_EXCEPTIONS, is_retryable_error
from common.config import ServiceConfig
from common.utils.time import utc_now_iso
from common.exceptions import BusinessError


@dataclass
class TaskWorkerMetrics:
    """性能指标"""
    tasks_processed: int = 0
    tasks_succeeded: int = 0
    tasks_failed: int = 0
    last_task_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "tasks_processed": self.tasks_processed,
            "tasks_succeeded": self.tasks_succeeded,
            "tasks_failed": self.tasks_failed,
            "last_task_at": self.last_task_at,
            "started_at": self.started_at,
        }


class TaskWorkerSync:
    """
    同步任务执行器
    
    优势：
    1. 代码简单 - 无需 async/await
    2. 易于调试 - 同步执行流程清晰
    3. 心跳自动 - 通过 HeartbeatSync 管理
    4. 进程隔离 - 崩溃不影响其他 Worker
    """
    
    name = "task-worker-sync"
    
    def __init__(
        self,
        topics: List[str],
        queue_service_url: str = None,
        gateway_url: str = None,
        poll_interval: float = None,
        timeout: float = None,
    ):
        self.topics = topics
        self.queue_service_url = queue_service_url or ServiceConfig.QUEUE_SERVICE_URL
        self.poll_interval = poll_interval if poll_interval is not None else ServiceConfig.POLL_INTERVAL
        self.timeout = timeout if timeout is not None else ServiceConfig.TASK_TIMEOUT
        self.worker_id = f"task-sync-{uuid.uuid4().hex[:8]}"
        
        self.gateway_url = gateway_url or ServiceConfig.GATEWAY_URL
        
        # 使用现有的同步 SDK
        self.client = TaskQueueClient(self.queue_service_url, timeout=timeout)  # 连接 Queue Service
        self.saga_client = SagaClient(self.queue_service_url, timeout=timeout)  # 用于 saga.trigger handler
        self.gateway_client = GatewayInternalClient(self.gateway_url, timeout=timeout)
        
        self._running = False
        self.metrics = TaskWorkerMetrics()
    
    def run(self):
        """主循环（同步）"""
        self._running = True
        self.metrics.started_at = utc_now_iso()
        
        self._log(f"Starting (worker_id: {self.worker_id}, topics: {self.topics})...")
        
        try:
            while self._running:
                try:
                    # 1. 认领任务
                    task = self._claim_task()
                    
                    if task:
                        # 2. 执行任务（带自动心跳）
                        self._execute_task_with_heartbeat(task)
                    else:
                        # 没任务就等待
                        time.sleep(self.poll_interval)
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    time.sleep(self.poll_interval)
        
        finally:
            self._running = False
            self.client.close()
            self.saga_client.close()
            self.gateway_client.close()
            self._log("Stopped")
    
    def shutdown(self):
        """优雅关闭"""
        self._log("Shutting down...")
        self._running = False
    
    def _claim_task(self) -> Optional[Dict[str, Any]]:
        """认领任务（同步）"""
        try:
            task = self.client.claim(self.topics, self.worker_id)
            return task
        except Exception as e:
            import traceback
            self._log(f"Failed to claim task: {e}", level="error")
            traceback.print_exc()
            return None
    
    def _execute_task_with_heartbeat(self, task: Dict[str, Any]):
        """
        执行任务（自动心跳）
        
        关键：使用 HeartbeatSync（with 语句），心跳在后台线程自动运行
        """
        task_id = task["id"]
        
        # 定义心跳函数
        def heartbeat_fn() -> bool:
            try:
                return self.client.heartbeat(task_id)
            except:
                return False
        
        # 定义失败回调
        def on_failure(count: int):
            if count >= 3:
                self._log(f"⚠️  Task {task_id} heartbeat failed {count} times", level="warning")
        
        # 使用心跳器（自动管理）
        try:
            with HeartbeatSync(
                task_id,
                heartbeat_fn,
                interval=10.0,
                on_failure=on_failure
            ):
                # 执行任务（同步）
                self._execute_task(task)
                
        except Exception as e:
            self._log(f"Task {task_id} failed: {e}", level="error")
            traceback.print_exc()
    
    def _execute_task(self, task: Dict[str, Any]):
        """
        执行任务（同步）
        
        这里的代码完全同步，无需 async/await
        
        错误处理策略：
        - BusinessError: 业务逻辑错误，不重试
        - RETRYABLE_EXCEPTIONS: 基础设施错误（网络、超时），重试
        - 其他 Exception: 未知错误，默认重试（保守策略）
        """
        task_id = task["id"]
        topic = task["topic"]
        
        self._log(f"Executing task {task_id} (topic: {topic})")
        
        try:
            # 调用 Handler（通过 Gateway API）
            result = self._call_handler(task)
            
            # 标记完成
            self.client.complete(task_id, result)
            
            self.metrics.tasks_succeeded += 1
            self._log(f"Task {task_id} completed")
            
        except BusinessError as e:
            # 业务逻辑错误，不重试
            error_msg = str(e)
            self.client.fail(task_id, error_msg, retry=False)
            
            self.metrics.tasks_failed += 1
            self._log(f"Task {task_id} failed (business error, no retry): {error_msg}", level="error")
            
        except RETRYABLE_EXCEPTIONS as e:
            # 基础设施错误（网络、超时等），重试
            error_msg = str(e)
            self.client.fail(task_id, error_msg, retry=True)
            
            self.metrics.tasks_failed += 1
            self._log(f"Task {task_id} failed (infra error, will retry): {error_msg}", level="error")
            
        except Exception as e:
            # 未知错误，检查是否可重试
            error_msg = str(e)
            should_retry = is_retryable_error(e)
            self.client.fail(task_id, error_msg, retry=should_retry)
            
            self.metrics.tasks_failed += 1
            retry_hint = "will retry" if should_retry else "no retry"
            self._log(f"Task {task_id} failed (unknown error, {retry_hint}): {error_msg}", level="error")
        
        finally:
            self.metrics.tasks_processed += 1
            self.metrics.last_task_at = utc_now_iso()
    
    def _call_handler(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        本地执行 Handler
        
        Handler 通过 GatewayInternalClient 调用 Gateway API 访问数据库
        """
        from task_queue.handlers import get_handler
        from task_queue.handlers.validation import validate_basic_payload
        
        topic = task["topic"]
        payload = task.get("payload")
        
        # 基础 payload 验证（确保是 dict）
        payload = validate_basic_payload(payload, topic)
        
        # 获取 handler
        handler = get_handler(topic)
        
        # 构建 handler 上下文
        ctx = {
            "gateway_url": self.gateway_client.gateway_url,
            "gateway_client": self.gateway_client,
            "saga_client": self.saga_client,
            "queue_service_url": self.queue_service_url,
        }
        
        # 执行 handler（同步）
        return handler(payload, ctx)
    
    def _log(self, message: str, level: str = "info"):
        """日志"""
        timestamp = utc_now_iso()
        prefix = f"[{timestamp}] [{self.worker_id}]"
        
        if level == "error":
            print(f"{prefix} ❌ {message}")
        elif level == "warning":
            print(f"{prefix} ⚠️  {message}")
        else:
            print(f"{prefix} {message}")


# ==================== 启动脚本 ====================

def start_worker(topics: List[str], queue_service_url: str = None, gateway_url: str = None):
    """启动一个 Worker（在当前进程）"""
    worker = TaskWorkerSync(topics, queue_service_url, gateway_url=gateway_url)
    worker.run()


def start_multiple_workers(
    num_workers: int = None,
    topics: List[str] = None,
    queue_service_url: str = None,
    gateway_url: str = None,
):
    """启动多个 Worker（多进程）"""
    from multiprocessing import Process
    
    if topics is None:
        # 自动从 handlers 注册表获取所有 topics
        from task_queue.handlers import get_all_topics
        topics = get_all_topics()
    
    processes = []
    
    print(f"Starting {num_workers} TaskWorkers (sync)...")
    
    for i in range(num_workers):
        p = Process(
            target=start_worker,
            args=(topics, queue_service_url, gateway_url),
            name=f"TaskWorker-{i+1}",
            daemon=False
        )
        p.start()
        processes.append(p)
        print(f"  TaskWorker {i+1} (PID: {p.pid})")
    
    # 等待所有进程
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\nShutting down workers...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join(timeout=5)


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import sys
    
    # 获取配置
    num_workers = ServiceConfig.NUM_WORKERS
    queue_service_url = ServiceConfig.QUEUE_SERVICE_URL
    gateway_url = ServiceConfig.GATEWAY_URL
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        num_workers = int(sys.argv[1])
    
    print("=" * 60)
    print("同步 TaskWorker (多进程)")
    print("=" * 60)
    print(f"Workers: {num_workers}")
    print(f"Queue Service: {queue_service_url}")
    print(f"Gateway: {gateway_url}")
    print("=" * 60)
    print()
    
    start_multiple_workers(
        num_workers=num_workers,
        queue_service_url=queue_service_url,
        gateway_url=gateway_url,
    )
