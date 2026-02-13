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
from common.utils.time import utc_now_iso


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
        """主循环（同步）
        
        两阶段提交流程：
        1. 查找 sending 消息（不改变状态）
        2. 创建 Saga（幂等，使用 message_id 作为幂等键）
        3. Saga 创建成功后，确认消息（sending → sent）
        
        如果 Saga 创建失败，消息保持 sending 状态，下次会重新处理。
        由于 Saga 创建是幂等的，重复处理不会产生重复 Saga。
        """
        self._running = True
        self.metrics.started_at = utc_now_iso()
        
        self._log(f"Starting (worker_id: {self.worker_id})...")
        
        try:
            while self._running:
                try:
                    # 1. 查找 sending 消息（不改变状态）
                    message = self._find_sending_message()
                    
                    if message:
                        # 2. 两阶段提交：先创建 Saga，成功后确认消息
                        self._process_message_two_phase(message)
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
        """查找 sending 消息（不改变状态）
        
        两阶段提交第一阶段：只查询，不更新状态。
        """
        try:
            return self.gateway_client.find_sending_message()
        except Exception as e:
            self._log(f"Failed to find message: {e}", level="error")
            return None
    
    def _confirm_message(self, message_id: str) -> bool:
        """确认消息（sending → sent）
        
        两阶段提交第二阶段：Saga 创建成功后调用。
        
        Returns:
            True 如果确认成功或消息已确认（幂等）
        """
        try:
            result = self.gateway_client.confirm_message(message_id)
            return result.get("success", False)
        except Exception as e:
            self._log(f"Failed to confirm message {message_id}: {e}", level="error")
            return False
    
    def _process_message_two_phase(self, message: Dict[str, Any]):
        """两阶段提交处理消息
        
        流程：
        1. 创建 Saga（幂等）
        2. Saga 创建成功后，确认消息
        
        如果 Saga 创建失败，消息保持 sending 状态，下次会重新处理。
        """
        msg_id = message.get("id")
        agent_id = message.get("agent_id")
        msg_type = message.get("type")
        metadata = message.get("metadata", {})
        
        self.metrics.messages_found += 1
        self.metrics.last_message_at = utc_now_iso()
        
        self._log(f"Found message {msg_id} (type={msg_type}, agent={agent_id})")
        
        # 根据消息类型创建 Saga
        saga_created = False
        
        if msg_type == "USER_MESSAGE":
            saga_created = self._create_message_process_saga(msg_id, agent_id, msg_type)
        elif msg_type == "SYSTEM_WAKE":
            saga_created = self._create_message_process_saga(msg_id, agent_id, msg_type)
        elif msg_type == "SUBAGENT_COMPLETED":
            saga_created = self._create_subagent_completed_saga(msg_id, agent_id, metadata)
        elif msg_type == "SPAWN_SUBAGENT":
            saga_created = self._create_spawn_subagent_saga(msg_id, agent_id, metadata)
        elif msg_type == "INTERRUPT":
            saga_created = self._handle_interrupt(msg_id, agent_id, metadata)
        else:
            self._log(f"Unknown message type, skipping: {msg_type}")
            # 未知类型也确认消息，避免永远卡住
            saga_created = True
        
        # 只有 Saga 创建成功后才确认消息
        if saga_created:
            confirmed = self._confirm_message(msg_id)
            if confirmed:
                self._log(f"Message {msg_id} confirmed (sending → sent)")
            else:
                # 确认失败不影响，因为 Saga 已创建
                # 下次处理时 Saga 会被幂等键拦截
                self._log(f"Message {msg_id} confirm failed (saga already created, will be idempotent)", level="warning")
        else:
            # Saga 创建失败，消息保持 sending 状态，下次会重新处理
            self._log(f"Saga creation failed for message {msg_id}, will retry", level="warning")
    
    def _create_message_process_saga(self, msg_id: str, agent_id: str, msg_type: str = "USER_MESSAGE") -> bool:
        """创建 message_process Saga（用于 USER_MESSAGE/SYSTEM_WAKE）
        
        Returns:
            True 如果 Saga 创建成功，False 如果失败
        """
        # Phase 4: Lifecycle hook — 用户消息自动计数
        if msg_type == "USER_MESSAGE":
            try:
                self.gateway_client.increment_drive_interaction(agent_id)
            except Exception:
                pass  # non-critical
        
        # 创建 MessageProcess Saga
        subagent_id = f"main-{agent_id[:8]}"
        
        try:
            saga_id = self.saga_client.start(
                saga_type="message_process",
                context={
                    "message_id": msg_id,
                    "agent_id": agent_id,
                    "subagent_id": subagent_id,
                    "trigger_type": "scheduled_wake" if msg_type == "SYSTEM_WAKE" else "user_message",
                },
                idempotency_key=f"message-process-{msg_id}",
            )
            
            self._log(f"Created MessageProcess Saga {saga_id} for message {msg_id}")
            self.metrics.sagas_created += 1
            return True
                
        except Exception as e:
            self._log(f"Failed to create saga: {e}", level="error")
            self.metrics.errors += 1
            return False
    
    def _create_subagent_completed_saga(self, msg_id: str, agent_id: str, metadata: Dict[str, Any]) -> bool:
        """创建 message_process Saga（用于 SUBAGENT_COMPLETED 通知）
        
        当 Sub SubAgent 完成时，通知 Parent SubAgent（通常是 Main）。
        统一走 message_process saga，与 USER_MESSAGE/SYSTEM_WAKE 流程一致。
        
        如果 Parent 正在运行，消息会被 ReactThink 的 context.read 读取。
        如果 Parent 已休眠，会触发唤醒流程。
        
        Returns:
            True 如果 Saga 创建成功，False 如果失败
        """
        parent_subagent_id = metadata.get("parent_subagent_id")
        subagent_id = metadata.get("subagent_id")
        
        # 如果没有指定 parent，默认通知 main
        if not parent_subagent_id:
            parent_subagent_id = f"main-{agent_id[:8]}"
        
        try:
            saga_id = self.saga_client.start(
                saga_type="message_process",
                context={
                    "message_id": msg_id,
                    "agent_id": agent_id,
                    "subagent_id": parent_subagent_id,  # 目标是 Parent SubAgent
                    "trigger_type": "subagent_completed",
                    "completed_subagent_id": subagent_id,
                },
                idempotency_key=f"message-process-{msg_id}",
            )
            
            self._log(f"Created MessageProcess Saga {saga_id} for subagent completion notification (target: {parent_subagent_id})")
            self.metrics.sagas_created += 1
            return True
                
        except Exception as e:
            self._log(f"Failed to create saga for subagent completion: {e}", level="error")
            self.metrics.errors += 1
            return False

    def _create_spawn_subagent_saga(self, msg_id: str, agent_id: str, metadata: Dict[str, Any]) -> bool:
        """创建 message_process Saga（用于 SubAgent spawn）
        
        统一走 message_process saga，与 USER_MESSAGE/SYSTEM_WAKE 流程一致。
        message_process 会调用 route_message -> get_or_create_runtime，
        然后触发 runtime_start saga。
        
        Returns:
            True 如果 Saga 创建成功，False 如果失败
        """
        subagent_id = metadata.get("subagent_id")
        trigger_id = metadata.get("trigger_id")
        initial_context = metadata.get("initial_context", [])
        
        if not subagent_id:
            self._log(f"SPAWN_SUBAGENT message {msg_id} missing subagent_id, skipping", level="error")
            self.metrics.errors += 1
            return False
        
        try:
            saga_id = self.saga_client.start(
                saga_type="message_process",
                context={
                    "message_id": msg_id,
                    "agent_id": agent_id,
                    "subagent_id": subagent_id,
                    "trigger_type": "spawn_subagent",
                    "trigger_id": trigger_id,
                    "initial_context": initial_context,
                },
                idempotency_key=f"message-process-{msg_id}",
            )
            
            self._log(f"Created MessageProcess Saga {saga_id} for subagent spawn {subagent_id}")
            self.metrics.sagas_created += 1
            return True
                
        except Exception as e:
            self._log(f"Failed to create saga for spawn: {e}", level="error")
            self.metrics.errors += 1
            return False
    
    def _handle_interrupt(self, msg_id: str, agent_id: str, metadata: Dict[str, Any]) -> bool:
        """处理 INTERRUPT 消息 - 调用 QS cancel-all API
        
        Returns:
            True 如果处理成功，False 如果失败
        """
        target_agent_id = metadata.get("target_agent_id")
        action = metadata.get("action", "cancel_all")
        
        try:
            # 调用 Queue Service cancel-all API
            # 使用 saga_client 的内部 _request 方法
            params = {"agent_id": target_agent_id} if target_agent_id else {}
            
            # 构建完整 URL 并发送请求
            session = self.saga_client._get_session()
            url = f"{self.saga_client.gateway_url}/api/queue/recover/cancel-all"
            resp = session.post(url, params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                cancelled_tasks = data.get("cancelled_tasks", 0)
                cancelled_sagas = data.get("cancelled_sagas", 0)
                self._log(f"INTERRUPT handled: cancelled {cancelled_tasks} tasks, {cancelled_sagas} sagas")
                return True
            else:
                self._log(f"Failed to handle INTERRUPT: {resp.status_code} - {resp.text}", level="error")
                self.metrics.errors += 1
                return False
                
        except Exception as e:
            self._log(f"Failed to handle INTERRUPT: {e}", level="error")
            self.metrics.errors += 1
            return False
    
    def _log(self, msg: str, level: str = "info"):
        """日志输出"""
        timestamp = utc_now_iso()
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
