"""
HealthMonitor

Background service that recovers stale tasks and monitors system health.

Responsibilities:
1. Monitor claimed tasks for heartbeat timeout
2. Reset stale tasks to 'pending' for re-claim
3. Monitor stuck 'sending' messages (v18)
4. Monitor stuck 'awaking' SubAgents (v18)
5. Log and track recovery metrics

This ensures the system can recover from worker crashes.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .gateway_client import GatewayClient


class HealthMonitor:
    """
    Background service that recovers stale tasks.
    
    A task is considered stale if:
    - status = 'claimed'
    - heartbeat_at < now - timeout_seconds
    
    Stale tasks are reset to 'pending' for re-claim via Gateway API.
    
    v18: Also monitors:
    - 'sending' messages stuck for too long
    - 'awaking' SubAgents stuck for too long
    """
    
    name = "health-monitor"
    
    def __init__(self, client: 'GatewayClient', config: Optional[Dict[str, Any]] = None):
        self.client = client
        self.config = config or {}
        
        # Configuration
        self.check_interval = self.config.get("check_interval", 30.0)  # seconds
        self.launcher_timeout = self.config.get("launcher_timeout", 60)  # seconds
        self.collector_timeout = self.config.get("collector_timeout", 60)  # seconds
        self.async_timeout = self.config.get("async_timeout", 300)  # 5 minutes
        
        # v18: Monitor queue health
        self.sending_timeout = self.config.get("sending_timeout", 30)  # seconds
        self.awaking_timeout = self.config.get("awaking_timeout", 60)  # seconds
        
        # Runtime state
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Metrics
        self.metrics = {
            "checks": 0,
            "recovered_launchers": 0,
            "recovered_collectors": 0,
            "recovered_async": 0,
            "stuck_sending": 0,  # v18
            "stuck_awaking": 0,  # v18
            "last_check_at": None,
            "started_at": None,
        }
    
    async def run(self):
        """Main monitor loop."""
        self._running = True
        self._shutdown_event.clear()
        self.metrics["started_at"] = datetime.utcnow().isoformat()
        
        self._log("Starting...")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    await self._check_and_recover()
                    self.metrics["checks"] += 1
                    self.metrics["last_check_at"] = datetime.utcnow().isoformat()
                except Exception as e:
                    self._log(f"Error in health check: {e}", level="error")
                
                await asyncio.sleep(self.check_interval)
        
        finally:
            self._running = False
            self._log("Stopped")
    
    async def _check_and_recover(self):
        """Check for stale tasks and recover them via Gateway API."""
        # Recover stale launcher tasks
        launcher_count = await self.client.recover_stale_tasks(
            task_type="launcher",
            timeout_seconds=self.launcher_timeout,
        )
        if launcher_count > 0:
            self.metrics["recovered_launchers"] += launcher_count
            self._log(f"Recovered {launcher_count} stale launcher task(s)")
        
        # Recover stale collector tasks
        collector_count = await self.client.recover_stale_tasks(
            task_type="collector",
            timeout_seconds=self.collector_timeout,
        )
        if collector_count > 0:
            self.metrics["recovered_collectors"] += collector_count
            self._log(f"Recovered {collector_count} stale collector task(s)")
        
        # Recover stale async tasks
        async_count = await self.client.recover_stale_tasks(
            task_type="async",
            timeout_seconds=self.async_timeout,
        )
        if async_count > 0:
            self.metrics["recovered_async"] += async_count
            self._log(f"Recovered {async_count} stale async task(s)")
        
        # v18: Check stuck sending messages
        try:
            stuck_sending = await self.client.get_stuck_sending_count(self.sending_timeout)
            if stuck_sending > 0:
                self.metrics["stuck_sending"] = stuck_sending
                self._log(f"Warning: {stuck_sending} message(s) stuck in 'sending' state", level="warn")
        except Exception as e:
            self._log(f"Error checking stuck sending: {e}", level="error")
        
        # v18: Check stuck awaking SubAgents
        try:
            stuck_awaking = await self.client.get_stuck_awaking_count(self.awaking_timeout)
            if stuck_awaking > 0:
                self.metrics["stuck_awaking"] = stuck_awaking
                self._log(f"Warning: {stuck_awaking} SubAgent(s) stuck in 'awaking' state", level="warn")
                # Reset stuck awaking to sleeping (failed to start)
                reset_count = await self.client.reset_stuck_awaking(self.awaking_timeout)
                if reset_count > 0:
                    self._log(f"Reset {reset_count} stuck awaking SubAgent(s) to sleeping")
        except Exception as e:
            self._log(f"Error checking stuck awaking: {e}", level="error")
    
    async def shutdown(self):
        """Initiate graceful shutdown."""
        self._log("Shutdown requested...")
        self._shutdown_event.set()
    
    def _log(self, message: str, level: str = "info"):
        """Log a message with service name prefix."""
        prefix = f"[{self.name}]"
        if level == "error":
            print(f"{prefix} ERROR: {message}")
        else:
            print(f"{prefix} {message}")
    
    def get_status(self) -> dict:
        """Get current monitor status."""
        return {
            "name": self.name,
            "running": self._running,
            "metrics": self.metrics,
        }
