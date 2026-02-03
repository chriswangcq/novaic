"""
Watchdog - 消息监视器

监视 sending 状态的消息，为每条消息创建 MessageProcess Saga。

职责：
1. 发现 sending 状态的消息
2. 为每条消息创建 MessageProcess Saga
3. 不包含任何业务逻辑（纯监视）

注意：
- Watchdog 不直接 claim 消息
- 所有业务逻辑在 MessageProcess Saga 中
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import traceback
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
    消息监视器
    
    职责：
    1. 发现 sending 状态的消息
    2. 为每条消息创建 MessageProcess Saga
    3. 不包含任何业务逻辑
    """
    
    name = "watchdog"
    
    def __init__(
        self,
        gateway_url: str = "http://127.0.0.1:19999",
        poll_interval: float = 0.1,
        timeout: float = 30.0,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.worker_id = f"wd-{uuid.uuid4().hex[:8]}"
        
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._client: Optional[httpx.AsyncClient] = None
        
        self.metrics = WatchdogMetrics()
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.gateway_url,
                timeout=self.timeout,
            )
        return self._client
    
    async def run(self):
        """主循环"""
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log(f"Starting (worker_id: {self.worker_id})...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # 1. 查找 sending 消息（不 claim）
                    message = await self._find_sending_message()
                    
                    if message:
                        await self._create_saga_for_message(message)
                    else:
                        await asyncio.sleep(self.poll_interval)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    self.metrics.errors += 1
                    await asyncio.sleep(self.poll_interval)
        
        finally:
            self._running = False
            if self._client:
                await self._client.aclose()
            self._log("Stopped")
    
    async def shutdown(self):
        """优雅关闭"""
        self._log("Shutting down...")
        self._shutdown_event.set()
    
    async def _find_sending_message(self) -> Optional[Dict[str, Any]]:
        """查找 sending 消息（不 claim）"""
        client = await self._get_client()
        
        try:
            resp = await client.get("/internal/messages/find-sending")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("message")
            return None
        except Exception as e:
            self._log(f"Failed to find message: {e}", level="error")
            return None
    
    async def _create_saga_for_message(self, message: Dict[str, Any]):
        """为消息创建 MessageProcess Saga"""
        msg_id = message.get("id")
        agent_id = message.get("agent_id")
        content = message.get("content", "")
        msg_type = message.get("type")
        
        self.metrics.messages_found += 1
        self.metrics.last_message_at = datetime.utcnow().isoformat()
        
        self._log(f"Found message {msg_id} (type={msg_type}, agent={agent_id})")
        
        # 只处理用户消息
        if msg_type != "USER_MESSAGE":
            return
        
        # 创建 MessageProcess Saga
        client = await self._get_client()
        
        subagent_id = f"main-{agent_id[:8]}"
        
        try:
            resp = await client.post(
                "/internal/tq/sagas/start",
                json={
                    "saga_type": "message_process",
                    "context": {
                        "message_id": msg_id,
                        "agent_id": agent_id,
                        "subagent_id": subagent_id,
                        "initial_context": [{"role": "user", "content": content}],
                    },
                    "idempotency_key": f"message-process-{msg_id}",
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                saga_id = data.get("saga_id")
                self._log(f"Created MessageProcess Saga {saga_id} for message {msg_id}")
                self.metrics.sagas_created += 1
            else:
                self._log(f"Failed to create saga: {resp.status_code}", level="error")
                self.metrics.errors += 1
                
        except Exception as e:
            self._log(f"Failed to create saga: {e}", level="error")
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
