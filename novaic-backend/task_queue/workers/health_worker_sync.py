"""
同步 HealthWorker - 健康监控

特点：
- 纯同步代码（无 async/await）
- 使用 SDK（GatewayInternalClient）
- 无需心跳（健康检查本身很轻量）
- 单线程串行（定期检查）

对比异步版本：
- 代码更简单（无 async/await）
- 逻辑完全一致
"""

import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import traceback

from task_queue.client import GatewayInternalClient


@dataclass
class HealthWorkerMetrics:
    """性能指标"""
    checks_performed: int = 0
    tasks_recovered: int = 0
    sagas_recovered: int = 0
    errors: int = 0
    last_check_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "checks_performed": self.checks_performed,
            "tasks_recovered": self.tasks_recovered,
            "sagas_recovered": self.sagas_recovered,
            "errors": self.errors,
            "last_check_at": self.last_check_at,
            "started_at": self.started_at,
        }


class HealthWorkerSync:
    """
    同步健康监控 Worker
    
    职责：
    1. 定期调用 Gateway 的恢复 API
    2. 恢复超时的任务和 Saga
    
    优势：
    - 纯同步代码，简单直接
    - 无需心跳（任务轻量）
    - 易于调试和维护
    """
    
    name = "health-worker-sync"
    
    def __init__(
        self,
        queue_service_url: str = "http://127.0.0.1:19997",  # 改为 Queue Service
        check_interval: float = 30.0,
        task_timeout: int = 60,
        saga_timeout: int = 120,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.check_interval = check_interval
        self.task_timeout = task_timeout
        self.saga_timeout = saga_timeout
        self.worker_id = f"health-sync-{uuid.uuid4().hex[:8]}"
        
        self._running = False
        
        # 使用 SDK（连接 Queue Service 进行恢复）
        self.gateway_client = GatewayInternalClient(queue_service_url, timeout=30.0)
        
        self.metrics = HealthWorkerMetrics()
    
    def run(self):
        """主循环（同步）"""
        self._running = True
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log(f"Starting (worker_id: {self.worker_id})...")
        
        try:
            while self._running:
                try:
                    # 执行健康检查
                    self._perform_check()
                    
                    # 等待下一次检查
                    time.sleep(self.check_interval)
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    self.metrics.errors += 1
                    time.sleep(self.check_interval)
        
        finally:
            self._running = False
            self.gateway_client.close()
            self._log("Stopped")
    
    def shutdown(self):
        """优雅关闭"""
        self._log("Shutting down...")
        self._running = False
    
    def _perform_check(self):
        """执行健康检查（同步）"""
        self.metrics.checks_performed += 1
        self.metrics.last_check_at = datetime.utcnow().isoformat()
        
        try:
            # 调用统一恢复 API
            data = self.gateway_client.recover_all(
                task_timeout=self.task_timeout,
                saga_timeout=self.saga_timeout,
            )
            
            tasks_recovered = data.get("tasks_recovered", 0)
            sagas_recovered = data.get("sagas_recovered", 0)
            
            self.metrics.tasks_recovered += tasks_recovered
            self.metrics.sagas_recovered += sagas_recovered
            
            if tasks_recovered > 0 or sagas_recovered > 0:
                self._log(
                    f"Recovered: {tasks_recovered} tasks, {sagas_recovered} sagas"
                )
                
        except Exception as e:
            self._log(f"Health check failed: {e}", level="error")
            self.metrics.errors += 1
    
    def _log(self, msg: str, level: str = "info"):
        """日志输出"""
        timestamp = datetime.utcnow().isoformat()
        prefix = f"[{timestamp}] [{self.worker_id}]"
        
        if level == "error":
            print(f"{prefix} ❌ {msg}")
        elif level == "warning":
            print(f"{prefix} ⚠️  {msg}")
        else:
            print(f"{prefix} {msg}")
    
    def get_metrics(self) -> dict:
        """获取指标"""
        return self.metrics.to_dict()


# ==================== 启动脚本 ====================

def start_worker(queue_service_url: str = "http://127.0.0.1:19997"):
    """启动 HealthWorker"""
    worker = HealthWorkerSync(queue_service_url)
    worker.run()


if __name__ == "__main__":
    import os
    
    queue_service_url = os.environ.get("QUEUE_SERVICE_URL", "http://127.0.0.1:19997")
    
    print("=" * 60)
    print("同步 HealthWorker (单线程)")
    print("=" * 60)
    print(f"Queue Service: {queue_service_url}")
    print("=" * 60)
    print()
    
    start_worker(gateway_url=gateway_url)
