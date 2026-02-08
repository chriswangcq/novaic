"""
同步 SchedulerWorker - 定时唤醒调度器

负责扫描 sleeping 且 wake_at 已过期的 SubAgent，
注入 SYSTEM_WAKE 消息触发正常唤醒流程。

特点：
- 纯同步代码（无 async/await）
- 通过 Gateway 内部 API 操作
- 单线程串行（轻量定时检查）
- 复用 Watchdog + MessageProcess 唤醒流程
"""

import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import traceback

from task_queue.client import GatewayInternalClient
from common.config import ServiceConfig


@dataclass
class SchedulerMetrics:
    """性能指标"""
    checks_performed: int = 0
    agents_woken: int = 0
    errors: int = 0
    last_check_at: Optional[str] = None
    started_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "checks_performed": self.checks_performed,
            "agents_woken": self.agents_woken,
            "errors": self.errors,
            "last_check_at": self.last_check_at,
            "started_at": self.started_at,
        }


class SchedulerWorkerSync:
    """
    同步定时唤醒 Worker
    
    职责：
    1. 定期扫描 sleeping 且 wake_at <= now 的 SubAgent
    2. 为每个到期 Agent 注入 SYSTEM_WAKE 消息
    3. Watchdog 自然发现消息并触发正常唤醒流程
    
    设计：
    - 不直接唤醒 Agent，而是注入消息复用已有流程
    - 幂等：重复注入消息不会导致问题（MessageProcess Saga 有幂等性保护）
    - 轻量：仅做 HTTP 调用，不执行业务逻辑
    """
    
    name = "scheduler-sync"
    
    def __init__(
        self,
        gateway_url: str = None,
        check_interval: float = 10.0,
    ):
        self.gateway_url = (gateway_url or ServiceConfig.GATEWAY_URL).rstrip("/")
        self.check_interval = check_interval
        self.worker_id = f"sched-sync-{uuid.uuid4().hex[:8]}"
        
        self._running = False
        self.gateway_client = GatewayInternalClient(self.gateway_url)
        
        self.metrics = SchedulerMetrics()
    
    def run(self):
        """主循环（同步）"""
        self._running = True
        self.metrics.started_at = datetime.utcnow().isoformat()
        
        self._log(f"Starting (worker_id: {self.worker_id})...")
        self._log(f"Gateway URL: {self.gateway_url}")
        self._log(f"Check interval: {self.check_interval}s")
        
        try:
            while self._running:
                try:
                    self._check_and_wake()
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
    
    def _check_and_wake(self):
        """扫描到期 Agent 并注入唤醒消息"""
        self.metrics.checks_performed += 1
        self.metrics.last_check_at = datetime.utcnow().isoformat()
        
        try:
            # 1. 查询到期的 SubAgent
            due_agents = self.gateway_client.get_due_for_wake()
            
            if not due_agents:
                return
            
            self._log(f"Found {len(due_agents)} agent(s) due for wake")
            
            # 2. 为每个到期 Agent 注入 SYSTEM_WAKE 消息
            for agent_info in due_agents:
                agent_id = agent_info.get("agent_id")
                subagent_id = agent_info.get("subagent_id")
                
                if not agent_id:
                    continue
                
                try:
                    result = self.gateway_client.inject_wake_message(
                        agent_id=agent_id,
                        metadata={
                            "wake_reason": "scheduled",
                            "subagent_id": subagent_id,
                            "wake_at": agent_info.get("wake_at"),
                            "handoff_notes": agent_info.get("handoff_notes"),
                        }
                    )
                    
                    if result.get("success"):
                        self.metrics.agents_woken += 1
                        self._log(
                            f"Injected wake message for agent={agent_id} "
                            f"subagent={subagent_id} "
                            f"(msg_id={result.get('message_id')})"
                        )
                    else:
                        self._log(
                            f"Failed to inject wake for agent={agent_id}: "
                            f"{result.get('error', 'unknown')}",
                            level="warning"
                        )
                        
                except Exception as e:
                    self._log(
                        f"Error waking agent={agent_id}: {e}",
                        level="error"
                    )
                    self.metrics.errors += 1
                    
        except Exception as e:
            self._log(f"Check failed: {e}", level="error")
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

def start_worker(gateway_url: str = None):
    """启动 SchedulerWorker"""
    worker = SchedulerWorkerSync(gateway_url=gateway_url)
    worker.run()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="同步 SchedulerWorker (定时唤醒)")
    parser.add_argument(
        "--gateway-url",
        default=ServiceConfig.GATEWAY_URL,
        help=f"Gateway URL (default: {ServiceConfig.GATEWAY_URL})",
    )
    parser.add_argument(
        "--check-interval",
        type=float,
        default=10.0,
        help="Check interval in seconds (default: 10.0)",
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("同步 SchedulerWorker (定时唤醒)")
    print("=" * 60)
    print(f"Gateway: {args.gateway_url}")
    print(f"Check interval: {args.check_interval}s")
    print("=" * 60)
    print()
    
    worker = SchedulerWorkerSync(
        gateway_url=args.gateway_url,
        check_interval=args.check_interval,
    )
    worker.run()
