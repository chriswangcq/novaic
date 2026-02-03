"""
MonitorWorker - 消息队列消费者

事件驱动的 Monitor 服务，消费 sending 队列：
1. CAS 认领一条 sending 消息 → sent
2. 尝试唤醒对应 SubAgent (sleeping/failed → awaking)
3. 如果唤醒成功，创建 runtime_launcher 任务

不再是轮询 unread 消息，而是消费消息状态队列。
"""

import asyncio
import json
import re
import signal
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import traceback

if TYPE_CHECKING:
    from .gateway_client import GatewayClient


@dataclass
class MonitorMetrics:
    """Monitor 性能指标"""
    messages_processed: int = 0
    subagents_woken: int = 0
    runtimes_created: int = 0
    failed: int = 0
    last_message_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "messages_processed": self.messages_processed,
            "subagents_woken": self.subagents_woken,
            "runtimes_created": self.runtimes_created,
            "failed": self.failed,
            "last_message_at": self.last_message_at,
            "started_at": self.started_at,
        }


class MonitorWorker:
    """
    消息队列消费者 - 消费 sending 状态的消息
    
    流程：
    1. claim_sending: CAS 认领一条消息 (sending → sent)
    2. 获取对应 SubAgent
    3. try_wake: CAS 唤醒 (sleeping/failed → awaking)
    4. 如果唤醒成功，创建 runtime_launcher 任务
    """
    
    name = "monitor"
    poll_interval = 0.1  # 100ms 轮询间隔
    
    def __init__(self, client: 'GatewayClient', config: Optional[Dict[str, Any]] = None):
        self.client = client
        self.config = config or {}
        self.worker_id = f"monitor-{uuid.uuid4().hex[:8]}"
        
        # Runtime state
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Metrics
        self.metrics = MonitorMetrics()
    
    async def run(self):
        """主循环：消费 sending 队列"""
        self._running = True
        self._shutdown_event.clear()
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        # Setup signal handlers
        self._setup_signals()
        
        self._log(f"Starting (worker_id: {self.worker_id})...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # 1. CAS 认领一条 sending 消息
                    message = await self.client.claim_sending_message()
                    
                    if message:
                        await self._process_message(message)
                    else:
                        # 队列为空，等待
                        await asyncio.sleep(self.poll_interval)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._log(f"Error in main loop: {e}", level="error")
                    traceback.print_exc()
                    self.metrics.failed += 1
                    await asyncio.sleep(self.poll_interval)
        
        finally:
            self._running = False
            self._log("Stopped")
    
    async def _process_message(self, message: Dict[str, Any]):
        """处理一条消息"""
        msg_id = message.get("id")
        agent_id = message.get("agent_id")
        msg_type = message.get("type")
        
        self.metrics.messages_processed += 1
        self.metrics.last_message_at = datetime.utcnow().isoformat()
        
        self._log(f"Processing message {msg_id} (type={msg_type}, agent={agent_id})")
        
        # 只处理用户消息触发的唤醒
        if msg_type != "USER_MESSAGE":
            return
        
        # 2. 获取 main SubAgent
        subagent = await self.client.get_main_subagent(agent_id)
        if not subagent:
            self._log(f"No SubAgent found for agent {agent_id}")
            return
        
        subagent_id = subagent.get("subagent_id", "main")
        status = subagent.get("status", "sleeping")
        
        # 3. 检查是否需要唤醒
        # - sleeping: 正常唤醒
        # - failed: 重试
        # - awaking: 正在启动，跳过
        # - awake: 已经在运行，跳过
        if status not in ("sleeping", "failed"):
            self._log(f"SubAgent {subagent_id} is {status}, skip")
            return
        
        # 4. 检查 wake_triggers
        wake_triggers = subagent.get("wake_triggers", [{"type": "user_response"}])
        if isinstance(wake_triggers, str):
            try:
                wake_triggers = json.loads(wake_triggers)
            except:
                wake_triggers = [{"type": "user_response"}]
        
        if not self._should_wake(wake_triggers, message):
            self._log(f"Message doesn't match wake triggers for {subagent_id}")
            return
        
        # 5. CAS 唤醒: sleeping/failed → awaking
        woke = await self.client.try_wake_subagent(
            agent_id, 
            subagent_id,
            target_status="awaking"
        )
        
        if not woke:
            self._log(f"SubAgent {subagent_id} already woken by another worker")
            return
        
        self.metrics.subagents_woken += 1
        self._log(f"SubAgent {subagent_id}: {status} → awaking")
        
        # 6. 创建 runtime_launcher 任务
        stage_id = f"stage-{uuid.uuid4().hex[:8]}"
        task_id = await self.client.create_task(
            task_type="launcher",
            task_subtype="runtime_launcher",
            runtime_id="pending",  # RuntimeLauncher 会创建真正的 runtime
            stage_id=stage_id,
            agent_id=agent_id,
            args={
                "agent_id": agent_id,
                "subagent_id": subagent_id,
            },
            idempotency_key=f"monitor-wake-{subagent_id}-{msg_id}",
        )
        
        if task_id:
            self.metrics.runtimes_created += 1
            self._log(f"Created runtime_launcher task {task_id} for {subagent_id}")
        else:
            self._log(f"runtime_launcher task already exists for {subagent_id}")
    
    def _should_wake(self, triggers: List[Dict[str, Any]], message: Dict[str, Any]) -> bool:
        """检查消息是否匹配唤醒触发器"""
        for trigger in triggers:
            trigger_type = trigger.get("type")
            
            if trigger_type == "user_response":
                # 任何用户消息都触发
                if message.get("type") == "USER_MESSAGE":
                    return True
            
            elif trigger_type == "keyword":
                # 关键词匹配
                pattern = trigger.get("pattern", "")
                if pattern:
                    try:
                        regex = re.compile(pattern, re.IGNORECASE)
                        content = message.get("content", "")
                        if regex.search(content):
                            return True
                    except re.error:
                        pass
        
        return False
    
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
        else:
            print(f"{prefix} {message}")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def get_status(self) -> dict:
        return {
            "name": self.name,
            "worker_id": self.worker_id,
            "running": self._running,
            "metrics": self.metrics.to_dict(),
        }
