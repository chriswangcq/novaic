"""
同步 Watchdog - 消息监视器

特点：
- 纯同步代码（无 async/await）
- 使用 SDK（SagaClient, GatewayInternalClient）
- 无需心跳（Watchdog 不执行长时间任务）
- 单线程串行（监视任务本身很轻量）

对比异步版本：
- 代码更简单（无 async/await）
- 逻辑完全一致
"""

import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

from task_queue.client import SagaClient, GatewayInternalClient
from common.config import ServiceConfig


@dataclass
class WatchdogMetrics:
    """性能指标"""
    messages_found: int = 0
    sagas_created: int = 0
    errors: int = 0
    last_message_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "messages_found": self.messages_found,
            "sagas_created": self.sagas_created,
            "errors": self.errors,
            "last_message_at": self.last_message_at,
            "started_at": self.started_at,
        }


class WatchdogSync:
    """
    同步消息监视器
    
    职责：
    1. 发现 sending 状态的消息
    2. 为每条消息创建 MessageProcess Saga
    3. 不包含任何业务逻辑
    
    优势：
    - 纯同步代码，简单直接
    - 无需心跳（任务轻量）
    - 易于调试和维护
    """
    
    name = "watchdog-sync"
    
    def __init__(
        self,
        gateway_url: str = None,
        queue_service_url: str = None,
        poll_interval: float = None,
        timeout: float = None,
    ):
        self.gateway_url = (gateway_url or ServiceConfig.GATEWAY_URL).rstrip("/")
        self.queue_service_url = (queue_service_url or ServiceConfig.QUEUE_SERVICE_URL).rstrip("/")
        self.poll_interval = poll_interval if poll_interval is not None else ServiceConfig.POLL_INTERVAL
        self.timeout = timeout if timeout is not None else ServiceConfig.HTTP_TIMEOUT
        self.worker_id = f"wd-sync-{uuid.uuid4().hex[:8]}"
        
        self._running = False
        
        # 使用 SDK
        self.saga_client = SagaClient(queue_service_url, timeout=timeout)
        self.gateway_client = GatewayInternalClient(gateway_url, timeout=timeout)
        
        self.metrics = WatchdogMetrics()
    
    def run(self):
        """主循环（同步）"""
        self._running = True
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log(f"Starting (worker_id: {self.worker_id})...")
        
        try:
            while self._running:
                try:
                    # 1. Claim 一条 sending 消息（sending → sent）
                    message = self._find_sending_message()
                    
                    if message:
                        # 2. 为已 claim 的消息创建 saga
                        self._create_saga_for_message(message)
                        # 立即处理下一条，不 sleep（批量处理）
                    else:
                        # 队列空了，休眠
                        time.sleep(self.poll_interval)
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    self.metrics.errors += 1
                    time.sleep(self.poll_interval)
        
        finally:
            self._running = False
            self.saga_client.close()
            self.gateway_client.close()
            self._log("Stopped")
    
    def shutdown(self):
        """优雅关闭"""
        self._log("Shutting down...")
        self._running = False
    
    def _find_sending_message(self) -> Optional[Dict[str, Any]]:
        """查找并 claim sending 消息（sending → sent）"""
        try:
            return self.gateway_client.claim_and_prepare_message()
        except Exception as e:
            self._log(f"Failed to find message: {e}", level="error")
            return None
    
    def _create_saga_for_message(self, message: Dict[str, Any]):
        """为消息创建 MessageProcess Saga"""
        msg_id = message.get("id")
        agent_id = message.get("agent_id")
        msg_type = message.get("type")
        
        self.metrics.messages_found += 1
        self.metrics.last_message_at = datetime.utcnow().isoformat()
        
        self._log(f"Found message {msg_id} (type={msg_type}, agent={agent_id})")
        
        # 只处理用户消息
        if msg_type != "USER_MESSAGE":
            return
        
        # 创建 MessageProcess Saga
        subagent_id = f"main-{agent_id[:8]}"
        
        try:
            saga_id = self.saga_client.start(
                saga_type="message_process",
                context={
                    "message_id": msg_id,
                    "agent_id": agent_id,
                    "subagent_id": subagent_id,
                },
                idempotency_key=f"message-process-{msg_id}",
            )
            
            self._log(f"Created MessageProcess Saga {saga_id} for message {msg_id}")
            self.metrics.sagas_created += 1
                
        except Exception as e:
            self._log(f"Failed to create saga: {e}", level="error")
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

def start_worker(
    gateway_url: str = None,
    queue_service_url: str = None,
):
    """启动 Watchdog"""
    worker = WatchdogSync(gateway_url, queue_service_url)
    worker.run()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="同步 Watchdog (单线程)")
    parser.add_argument(
        "--gateway-url",
        default=ServiceConfig.GATEWAY_URL,
        help=f"Gateway URL (default: {ServiceConfig.GATEWAY_URL})",
    )
    parser.add_argument(
        "--queue-service-url",
        default=ServiceConfig.QUEUE_SERVICE_URL,
        help=f"Queue Service URL (default: {ServiceConfig.QUEUE_SERVICE_URL})",
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("同步 Watchdog (单线程)")
    print("=" * 60)
    print(f"Gateway: {args.gateway_url}")
    print(f"Queue Service: {args.queue_service_url}")
    print("=" * 60)
    print()
    
    start_worker(
        gateway_url=args.gateway_url,
        queue_service_url=args.queue_service_url,
    )
