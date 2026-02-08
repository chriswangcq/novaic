"""
Watchdog - 消息监视器 (Agent 唤醒系统)

监视 sending 状态的消息，为每条消息创建 MessageProcess Saga。

架构定位：
- Watchdog 是 Gateway 和 Queue Service 之间的桥梁
- 监控 Gateway 的消息 → 在 Queue Service 创建 Saga

职责：
1. 发现 sending 状态的消息 (调用 Gateway API)
2. 为每条消息创建 MessageProcess Saga (调用 Queue Service API)
3. 不包含任何业务逻辑（纯监视 + 触发）

交互：
- Gateway: /internal/messages/claim-and-prepare (获取消息)
- Queue Service: /api/queue/sagas/start (创建 saga)

注意：
- Watchdog 不直接 claim 消息
- 所有业务逻辑在 MessageProcess Saga 中
"""

import time
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import traceback
from common.config import ServiceConfig
import httpx


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


class Watchdog:
    """
    消息监视器 (Agent 唤醒系统)
    
    架构定位：Gateway 和 Queue Service 之间的桥梁
    
    职责：
    1. 发现 sending 状态的消息 (调用 Gateway)
    2. 为每条消息创建 MessageProcess Saga (调用 Queue Service)
    3. 不包含任何业务逻辑
    
    交互：
    - Gateway: /internal/messages/claim-and-prepare
    - Queue Service: /api/queue/sagas/start
    """
    
    name = "watchdog"
    
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
        self.worker_id = f"wd-{uuid.uuid4().hex[:8]}"
        
        self._running = False
        self._shutdown_event = threading.Event()
        self._gateway_client: Optional[httpx.Client] = None
        self._queue_client: Optional[httpx.Client] = None
        
        self.metrics = WatchdogMetrics()
    
    def _get_gateway_client(self) -> httpx.Client:
        """获取 Gateway HTTP 客户端"""
        if self._gateway_client is None:
            self._gateway_client = httpx.Client(
                base_url=self.gateway_url,
                timeout=self.timeout,
            )
        return self._gateway_client
    
    def _get_queue_client(self) -> httpx.Client:
        """获取 Queue Service HTTP 客户端"""
        if self._queue_client is None:
            self._queue_client = httpx.Client(
                base_url=self.queue_service_url,
                timeout=self.timeout,
            )
        return self._queue_client
    
    def run(self):
        """主循环"""
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log(f"Starting (worker_id: {self.worker_id})...")
        self._log(f"Gateway URL: {self.gateway_url}")
        self._log(f"Queue Service URL: {self.queue_service_url}")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # 1. Claim一条sending消息（sending → sent）- 调用 Gateway
                    message = self._find_sending_message()
                    
                    if message:
                        # 2. 为已claim的消息创建saga - 调用 Queue Service
                        self._create_saga_for_message(message)
                        # 立即处理下一条，不sleep（批量处理）
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
            if self._gateway_client:
                self._gateway_client.close()
            if self._queue_client:
                self._queue_client.close()
            self._log("Stopped")
    
    def shutdown(self):
        """优雅关闭"""
        self._log("Shutting down...")
        self._shutdown_event.set()
    
    def _find_sending_message(self) -> Optional[Dict[str, Any]]:
        """查找并claim sending消息（sending → sent）- 调用 Gateway"""
        client = self._get_gateway_client()
        
        try:
            resp = client.post("/internal/messages/claim-and-prepare")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("message")
            return None
        except Exception as e:
            self._log(f"Failed to find message from Gateway: {e}", level="error")
            return None
    
    def _create_saga_for_message(self, message: Dict[str, Any]):
        """
        根据消息类型执行对应操作 - 调用 Queue Service
        
        消息类型 → 操作映射：
        - USER_MESSAGE → 创建 message_process saga
        - SPAWN_SUBAGENT → 创建 runtime_start saga
        - INTERRUPT → 调用 QS cancel API (不创建 saga)
        """
        msg_id = message.get("id")
        agent_id = message.get("agent_id")
        content = message.get("content", "")
        msg_type = message.get("type")
        metadata = message.get("metadata", {})
        
        self.metrics.messages_found += 1
        self.metrics.last_message_at = datetime.utcnow().isoformat()
        
        self._log(f"Found message {msg_id} (type={msg_type}, agent={agent_id})")
        
        # 根据消息类型分发到不同的处理逻辑
        if msg_type == "USER_MESSAGE":
            self._create_message_process_saga(msg_id, agent_id, msg_type)
        elif msg_type == "SYSTEM_WAKE":
            self._create_message_process_saga(msg_id, agent_id, msg_type)
        elif msg_type == "SPAWN_SUBAGENT":
            self._create_runtime_start_saga(msg_id, agent_id, metadata)
        elif msg_type == "INTERRUPT":
            self._handle_interrupt(msg_id, agent_id, metadata)
        else:
            self._log(f"Unknown message type, skipping: {msg_type}")
    
    def _create_message_process_saga(self, msg_id: str, agent_id: str, msg_type: str = "USER_MESSAGE"):
        """创建 message_process Saga"""
        client = self._get_queue_client()
        subagent_id = f"main-{agent_id[:8]}"
        
        try:
            resp = client.post(
                "/api/queue/sagas/start",
                json={
                    "saga_type": "message_process",
                    "context": {
                        "message_id": msg_id,
                        "agent_id": agent_id,
                        "subagent_id": subagent_id,
                        "trigger_type": "scheduled_wake" if msg_type == "SYSTEM_WAKE" else "user_message",
                    },
                    "idempotency_key": f"message-process-{msg_id}",
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                saga_id = data.get("saga_id")
                self._log(f"Created message_process Saga {saga_id} for message {msg_id}")
                self.metrics.sagas_created += 1
            else:
                self._log(f"Failed to create message_process saga: {resp.status_code} - {resp.text}", level="error")
                self.metrics.errors += 1
                
        except Exception as e:
            self._log(f"Failed to create message_process saga: {e}", level="error")
            self.metrics.errors += 1
    
    def _create_runtime_start_saga(self, msg_id: str, agent_id: str, metadata: Dict[str, Any]):
        """创建 runtime_start Saga (用于 SubAgent spawn)"""
        client = self._get_queue_client()
        
        subagent_id = metadata.get("subagent_id")
        trigger_id = metadata.get("trigger_id")
        initial_context = metadata.get("initial_context", [])
        
        if not subagent_id:
            self._log(f"SPAWN_SUBAGENT message {msg_id} missing subagent_id, skipping", level="error")
            self.metrics.errors += 1
            return
        
        try:
            resp = client.post(
                "/api/queue/sagas/start",
                json={
                    "saga_type": "runtime_start",
                    "context": {
                        "agent_id": agent_id,
                        "subagent_id": subagent_id,
                        "trigger_id": trigger_id,
                        "initial_context": initial_context,
                    },
                    "idempotency_key": f"runtime-start-{trigger_id}",
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                saga_id = data.get("saga_id")
                self._log(f"Created runtime_start Saga {saga_id} for subagent {subagent_id}")
                self.metrics.sagas_created += 1
            else:
                self._log(f"Failed to create runtime_start saga: {resp.status_code} - {resp.text}", level="error")
                self.metrics.errors += 1
                
        except Exception as e:
            self._log(f"Failed to create runtime_start saga: {e}", level="error")
            self.metrics.errors += 1
    
    def _handle_interrupt(self, msg_id: str, agent_id: str, metadata: Dict[str, Any]):
        """处理 INTERRUPT 消息 - 调用 QS cancel API"""
        client = self._get_queue_client()
        
        target_agent_id = metadata.get("target_agent_id")
        action = metadata.get("action", "cancel_all")
        
        try:
            # 调用 Queue Service cancel-all API
            resp = client.post(
                "/api/queue/recover/cancel-all",
                params={"agent_id": target_agent_id} if target_agent_id else {}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                cancelled_tasks = data.get("cancelled_tasks", 0)
                cancelled_sagas = data.get("cancelled_sagas", 0)
                self._log(f"INTERRUPT handled: cancelled {cancelled_tasks} tasks, {cancelled_sagas} sagas")
            else:
                self._log(f"Failed to handle INTERRUPT: {resp.status_code} - {resp.text}", level="error")
                self.metrics.errors += 1
                
        except Exception as e:
            self._log(f"Failed to handle INTERRUPT: {e}", level="error")
            self.metrics.errors += 1
    
    def _log(self, msg: str, level: str = "info"):
        """日志输出"""
        prefix = f"[{self.name}]"
        if level == "error":
            print(f"{prefix} ERROR: {msg}")
        else:
            print(f"{prefix} {msg}")
    
    def get_metrics(self) -> dict:
        """获取指标"""
        return self.metrics.to_dict()


# 保留旧名称的别名，用于向后兼容
MessageWorkerV2 = Watchdog
