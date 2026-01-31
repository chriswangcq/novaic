"""
Worker Process

Unified Worker model that can act as Agent (thinking) or Executor (executing).
Uses asyncio for internal concurrency to handle multiple IO-bound tasks.

v11: Created for multi-process architecture.
"""

import asyncio
import json
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Set, Callable, Awaitable
from enum import Enum

import aiohttp

# Handle both relative import (when running as module) and absolute import (PyInstaller)
try:
    from .id_generator import IDGenerator
except ImportError:
    from worker.id_generator import IDGenerator


class WorkerState(str, Enum):
    """Worker lifecycle states."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class WorkerConfig:
    """Worker configuration."""
    
    # Gateway connection
    gateway_url: str = "http://localhost:9527"
    
    # Concurrency
    max_concurrent: int = 10
    
    # Timeouts
    claim_timeout: float = 5.0
    execute_timeout: float = 300.0  # 5 minutes
    heartbeat_interval: float = 30.0
    
    # Retry
    reconnect_delay: float = 5.0
    max_reconnect_attempts: int = 10
    
    # Worker ID (auto-generated if not provided)
    worker_id: Optional[str] = None


class Worker:
    """
    Unified Worker process for the multi-process architecture.
    
    Features:
    - SSE subscription for real-time events
    - Asyncio-based concurrency for IO-bound tasks
    - Automatic reconnection on connection loss
    - Heartbeat reporting
    - Graceful shutdown handling
    
    Usage:
        config = WorkerConfig(gateway_url="http://localhost:9527")
        worker = Worker(config)
        
        # Register handlers
        worker.register_message_handler(handle_message)
        worker.register_task_handler(handle_task)
        
        # Run
        await worker.run()
    """
    
    def __init__(self, config: Optional[WorkerConfig] = None):
        """
        Initialize Worker.
        
        Args:
            config: Worker configuration
        """
        self.config = config or WorkerConfig()
        self.worker_id = self.config.worker_id or IDGenerator.worker_id()
        
        # State
        self._state = WorkerState.STOPPED
        self._current_tasks: Set[str] = set()
        self._running_tasks: Dict[str, asyncio.Task] = {}
        
        # Task handlers (v12: message handler removed, Master drives everything)
        self._task_handlers: Dict[str, Callable] = {}
        
        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Control
        self._shutdown_event = asyncio.Event()
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    @property
    def state(self) -> WorkerState:
        """Current worker state."""
        return self._state
    
    @property
    def current_task_count(self) -> int:
        """Number of currently processing tasks."""
        return len(self._current_tasks)
    
    @property
    def has_capacity(self) -> bool:
        """Whether worker can accept more tasks."""
        return self.current_task_count < self.config.max_concurrent
    
    # ==================== Handler Registration ====================
    
    def register_task_handler(
        self,
        task_type: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Any]],
    ):
        """
        Register handler for task events.
        
        Args:
            task_type: Task type (think, tool_call, reply)
            handler: Async function that executes tasks
        """
        self._task_handlers[task_type] = handler
    
    # ==================== Main Loop ====================
    
    async def run(self):
        """
        Main worker loop.
        
        Connects to Gateway SSE and processes events until shutdown.
        """
        self._state = WorkerState.STARTING
        self._shutdown_event.clear()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Create HTTP session
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        
        try:
            # Register with Gateway
            await self._register()
            
            self._state = WorkerState.RUNNING
            
            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Main event loop with reconnection
            reconnect_attempts = 0
            while not self._shutdown_event.is_set():
                try:
                    await self._event_loop()
                    reconnect_attempts = 0  # Reset on successful connection
                except aiohttp.ClientError as e:
                    reconnect_attempts += 1
                    if reconnect_attempts >= self.config.max_reconnect_attempts:
                        print(f"[Worker {self.worker_id}] Max reconnect attempts reached, shutting down")
                        break
                    
                    print(f"[Worker {self.worker_id}] Connection error: {e}, reconnecting in {self.config.reconnect_delay}s...")
                    await asyncio.sleep(self.config.reconnect_delay)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[Worker {self.worker_id}] Unexpected error: {e}")
                    await asyncio.sleep(self.config.reconnect_delay)
        
        finally:
            self._state = WorkerState.STOPPING
            await self._shutdown()
    
    async def _event_loop(self):
        """
        SSE event processing loop.
        
        Subscribes to Gateway SSE and handles events.
        """
        url = f"{self.config.gateway_url}/api/worker/events?worker_id={self.worker_id}"
        
        async with self._session.get(url) as response:
            if response.status != 200:
                raise aiohttp.ClientError(f"SSE connection failed: {response.status}")
            
            print(f"[Worker {self.worker_id}] Connected to Gateway SSE")
            
            # Process SSE stream
            buffer = ""
            async for chunk in response.content:
                if self._shutdown_event.is_set():
                    break
                
                buffer += chunk.decode("utf-8")
                
                # Process complete events
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    await self._process_sse_event(event_str)
    
    async def _process_sse_event(self, event_str: str):
        """
        Process a single SSE event.
        
        Args:
            event_str: Raw SSE event string
        """
        if not event_str.strip() or event_str.startswith(":"):
            return  # Keepalive comment
        
        # Parse SSE format
        event_type = "message"
        data = None
        
        for line in event_str.split("\n"):
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    data = line[5:].strip()
        
        if data is None:
            return
        
        # Handle event based on type
        if event_type == "new_message":
            await self._handle_new_message(data)
        elif event_type == "new_task":
            await self._handle_new_task(data)
        elif event_type == "task_result":
            await self._handle_task_result(data)
        elif event_type == "round_complete":
            await self._handle_round_complete(data)
        elif event_type == "worker_shutdown":
            print(f"[Worker {self.worker_id}] Received shutdown signal")
            self._shutdown_event.set()
        elif event_type == "heartbeat":
            pass  # Ignored
    
    # ==================== Event Handlers ====================
    
    async def _handle_new_message(self, data: Dict[str, Any]):
        """Handle new message event (v12: Not used, Master creates think tasks)."""
        # In Master-driven architecture, messages are handled by Master creating think tasks
        # This method is kept for potential future use but does nothing
        pass
    
    async def _handle_new_task(self, data: Dict[str, Any]):
        """Handle new task event."""
        if not self.has_capacity:
            return
        
        task_id = data.get("id")
        task_type = data.get("type")
        
        if not task_id or not task_type:
            return
        
        # Check if we have a handler for this type
        handler = self._task_handlers.get(task_type)
        if not handler:
            return
        
        # Try to claim
        claimed = await self._claim_task(task_id)
        if claimed:
            # Start execution in background
            task = asyncio.create_task(
                self._execute_task(task_id, claimed, handler)
            )
            self._running_tasks[task_id] = task
    
    async def _handle_task_result(self, data: Dict[str, Any]):
        """Handle task result event."""
        # Used by Agent role to know when its mcpcalls complete
        task_id = data.get("id")
        status = data.get("status")
        
        # Notify any waiting coroutines
        # (Implementation depends on how Agent handler waits for results)
    
    async def _handle_round_complete(self, data: Dict[str, Any]):
        """Handle round complete event."""
        subagent_id = data.get("subagent_id")
        round_id = data.get("round_id")
        
        # Notify Agent handler that round is complete
        # (Implementation depends on how Agent handler waits for round)
    
    # ==================== Claim Operations ====================
    
    async def _claim_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Try to claim a message.
        
        Returns:
            Message data if claimed, None otherwise
        """
        try:
            async with self._session.post(
                f"{self.config.gateway_url}/api/claim/message/{message_id}",
                json={"worker_id": self.worker_id},
                timeout=aiohttp.ClientTimeout(total=self.config.claim_timeout),
            ) as response:
                result = await response.json()
                
                if result.get("claimed"):
                    self._current_tasks.add(message_id)
                    return result.get("message")
                
                return None
        except Exception as e:
            print(f"[Worker {self.worker_id}] Claim message error: {e}")
            return None
    
    async def _claim_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Try to claim a task.
        
        Returns:
            Task data if claimed, None otherwise
        """
        try:
            async with self._session.post(
                f"{self.config.gateway_url}/api/claim/task/{task_id}",
                json={"worker_id": self.worker_id},
                timeout=aiohttp.ClientTimeout(total=self.config.claim_timeout),
            ) as response:
                result = await response.json()
                
                if result.get("claimed"):
                    self._current_tasks.add(task_id)
                    return result.get("task")
                
                return None
        except Exception as e:
            print(f"[Worker {self.worker_id}] Claim task error: {e}")
            return None
    
    # ==================== Processing ====================
    
    # v12: _process_message removed - Master creates think tasks instead
    
    async def _execute_task(
        self,
        task_id: str,
        task: Dict[str, Any],
        handler: Callable,
    ):
        """
        Execute a claimed task.
        
        Args:
            task_id: Task ID
            task: Task data
            handler: Handler function
        """
        try:
            result = await asyncio.wait_for(
                handler(task, gateway_url=self.config.gateway_url),
                timeout=self.config.execute_timeout,
            )
            
            # Submit result
            await self._submit_result(task_id, "done", result=result)
            
        except asyncio.TimeoutError:
            print(f"[Worker {self.worker_id}] Task {task_id} timed out")
            await self._submit_result(task_id, "timeout")
            
        except Exception as e:
            print(f"[Worker {self.worker_id}] Task execution error: {e}")
            import traceback
            traceback.print_exc()
            await self._submit_result(task_id, "failed", error=str(e))
            
        finally:
            self._current_tasks.discard(task_id)
            self._running_tasks.pop(task_id, None)
    
    async def _release_message(self, message_id: str):
        """Release a claimed message."""
        try:
            await self._session.post(
                f"{self.config.gateway_url}/api/claim/message/{message_id}/release",
                json={"worker_id": self.worker_id},
            )
        except Exception as e:
            print(f"[Worker {self.worker_id}] Release message error: {e}")
    
    async def _submit_result(
        self,
        task_id: str,
        status: str,
        result: Any = None,
        error: Optional[str] = None,
    ):
        """Submit task execution result."""
        try:
            await self._session.post(
                f"{self.config.gateway_url}/api/result/{task_id}",
                json={
                    "status": status,
                    "result": result,
                    "error": error,
                },
            )
        except Exception as e:
            print(f"[Worker {self.worker_id}] Submit result error: {e}")
    
    # ==================== Heartbeat ====================
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to Gateway."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Worker {self.worker_id}] Heartbeat error: {e}")
    
    async def _send_heartbeat(self):
        """Send heartbeat to Gateway."""
        # This would update worker_processes table via an API
        # For now, just log
        pass
    
    # ==================== Registration ====================
    
    async def _register(self):
        """Register worker with Gateway."""
        print(f"[Worker {self.worker_id}] Registering with Gateway")
        # This would call an API to register in worker_processes table
    
    async def _unregister(self):
        """Unregister worker from Gateway."""
        print(f"[Worker {self.worker_id}] Unregistering from Gateway")
        # This would call an API to update worker_processes table
    
    # ==================== Shutdown ====================
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(self.shutdown())
                )
    
    async def shutdown(self):
        """Initiate graceful shutdown."""
        print(f"[Worker {self.worker_id}] Shutdown initiated")
        self._shutdown_event.set()
    
    async def _shutdown(self):
        """Perform shutdown cleanup."""
        self._state = WorkerState.STOPPING
        
        # Cancel heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Wait for running tasks (with timeout)
        if self._running_tasks:
            print(f"[Worker {self.worker_id}] Waiting for {len(self._running_tasks)} tasks to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._running_tasks.values(), return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                print(f"[Worker {self.worker_id}] Some tasks did not complete in time")
        
        # Unregister
        await self._unregister()
        
        # Close session
        if self._session:
            await self._session.close()
        
        self._state = WorkerState.STOPPED
        print(f"[Worker {self.worker_id}] Shutdown complete")


# ==================== Entry Point ====================

async def run_worker(config: Optional[WorkerConfig] = None):
    """
    Run a Worker process.
    
    This is the main entry point for Worker processes.
    
    v12/v2.5: Master-driven architecture - Workers are truly stateless.
    Master creates tasks, Workers claim and execute single tasks.
    
    Task types:
    - think: LLM thinking (Agent role)
    - tool_call: MCP tool execution (Executor role)
    - reply: Send reply to user (Executor role)
    
    Note: subagent task type removed in v2.5 - SubAgents are created
    via context_call MCP tool using Master API.
    
    Args:
        config: Worker configuration
    """
    worker = Worker(config)
    
    # Register task handlers for Master-driven architecture
    # v2.8: 只有 think 和 tool_call，所有操作（包括 reply）都走 MCP 工具
    from .executor_handler import handle_tool_call
    from .think_handler import handle_think
    
    worker.register_task_handler("think", handle_think)  # Think task from Master
    worker.register_task_handler("tool_call", handle_tool_call)  # 所有 MCP 工具调用
    
    await worker.run()


if __name__ == "__main__":
    # Allow running directly: python -m worker.worker
    import argparse
    
    parser = argparse.ArgumentParser(description="Run NovAIC Worker")
    parser.add_argument("--gateway", default="http://localhost:9527", help="Gateway URL")
    parser.add_argument("--max-concurrent", type=int, default=10, help="Max concurrent tasks")
    parser.add_argument("--worker-id", help="Worker ID (auto-generated if not provided)")
    
    args = parser.parse_args()
    
    config = WorkerConfig(
        gateway_url=args.gateway,
        max_concurrent=args.max_concurrent,
        worker_id=args.worker_id,
    )
    
    asyncio.run(run_worker(config))
