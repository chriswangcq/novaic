"""
Master - Core Scheduler

The central orchestrator for the multi-process architecture.
Manages Agent Runtimes, drives Rounds, and coordinates Workers.

v2.10: Master runs as separate service, calls Gateway via HTTP.
"""

import asyncio
import time
import httpx
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class MasterConfig:
    """Configuration for Master."""
    monitor_interval: float = 1.0  # seconds
    scheduler_interval: float = 0.1  # seconds
    max_rounds_per_runtime: int = 50


class GatewayClient:
    """HTTP client for calling Gateway (Backend) and MCP Gateway internal APIs."""
    
    def __init__(self, gateway_url: str, mcp_gateway_url: Optional[str] = None):
        self.gateway_url = gateway_url.rstrip("/")
        self.mcp_gateway_url = (mcp_gateway_url or gateway_url).rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
    
    async def start(self):
        """Start the HTTP client."""
        # Disable system proxy to avoid issues with local Gateway
        self._client = httpx.AsyncClient(timeout=30.0, trust_env=False)
    
    async def stop(self):
        """Stop the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("GatewayClient not started")
        return self._client
    
    # ==================== Runtime Operations ====================
    
    async def get_active_runtimes(self) -> List[Dict[str, Any]]:
        resp = await self.client.get(f"{self.gateway_url}/internal/runtimes/active")
        resp.raise_for_status()
        return resp.json().get("runtimes", [])
    
    async def get_runtime(self, subagent_id: str) -> Optional[Dict[str, Any]]:
        resp = await self.client.get(f"{self.gateway_url}/internal/runtimes/{subagent_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    
    async def create_main_runtime(self, agent_id: str) -> Dict[str, Any]:
        resp = await self.client.post(
            f"{self.gateway_url}/internal/runtimes/main",
            json={"agent_id": agent_id}
        )
        resp.raise_for_status()
        return resp.json()
    
    async def create_sub_runtime(
        self,
        agent_id: str,
        parent_subagent_id: str,
        initial_context: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        resp = await self.client.post(
            f"{self.gateway_url}/internal/runtimes/sub",
            json={
                "agent_id": agent_id,
                "parent_subagent_id": parent_subagent_id,
                "initial_context": initial_context or [],
            }
        )
        resp.raise_for_status()
        return resp.json()
    
    async def update_runtime(self, subagent_id: str, **kwargs):
        """Update runtime fields (phase, pending_actions, context, mcp_url, status, error)."""
        resp = await self.client.patch(
            f"{self.gateway_url}/internal/runtimes/{subagent_id}",
            json=kwargs
        )
        resp.raise_for_status()
    
    async def wake_runtime(self, subagent_id: str) -> bool:
        """Wake a sleeping runtime (atomic CAS).
        
        Returns:
            True if woken successfully, False if already active or not found.
        """
        resp = await self.client.post(f"{self.gateway_url}/internal/runtimes/{subagent_id}/wake")
        resp.raise_for_status()
        return resp.json().get("success", True)
    
    async def advance_round(self, subagent_id: str, expected_round_num: int = None) -> Optional[str]:
        """Advance runtime to next round (with optional CAS).
        
        Args:
            subagent_id: Runtime ID
            expected_round_num: If provided, only advance if current round matches (CAS)
            
        Returns:
            New round_id if advanced, None if CAS conflict or runtime not found.
        """
        data = {}
        if expected_round_num is not None:
            data["expected_round_num"] = expected_round_num
        
        resp = await self.client.post(
            f"{self.gateway_url}/internal/runtimes/{subagent_id}/advance",
            json=data if data else None
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("round_id") if result.get("success", True) else None
    
    async def try_claim_phase(self, subagent_id: str, expected_phase: str, new_phase: str) -> bool:
        """Atomically claim a phase transition (CAS).
        
        Used to prevent race conditions where multiple Masters try to
        process the same runtime's results simultaneously.
        
        Returns:
            True if claimed, False if CAS failed (phase didn't match).
        """
        resp = await self.client.post(
            f"{self.gateway_url}/internal/runtimes/{subagent_id}/claim-phase",
            json={"expected_phase": expected_phase, "new_phase": new_phase}
        )
        resp.raise_for_status()
        return resp.json().get("success", False)
    
    async def delete_runtime(self, subagent_id: str):
        resp = await self.client.delete(f"{self.gateway_url}/internal/runtimes/{subagent_id}")
        resp.raise_for_status()
    
    async def get_main_runtime(self, agent_id: str) -> Optional[Dict[str, Any]]:
        resp = await self.client.get(f"{self.gateway_url}/internal/runtimes/main/{agent_id}")
        resp.raise_for_status()
        return resp.json().get("runtime")
    
    # ==================== Task Operations ====================
    
    async def get_tasks(self, ids: List[str] = None, status: str = None) -> List[Dict[str, Any]]:
        params = {}
        if ids:
            params["ids"] = ",".join(ids)
        if status:
            params["status"] = status
        resp = await self.client.get(f"{self.gateway_url}/internal/tasks", params=params)
        resp.raise_for_status()
        return resp.json().get("tasks", [])
    
    async def create_task(self, **kwargs) -> bool:
        """Create task. Returns False if idempotency conflict."""
        resp = await self.client.post(f"{self.gateway_url}/internal/tasks", json=kwargs)
        if resp.status_code == 409:
            return False
        resp.raise_for_status()
        return True
    
    async def update_task(self, task_id: str, **kwargs):
        resp = await self.client.patch(f"{self.gateway_url}/internal/tasks/{task_id}", json=kwargs)
        resp.raise_for_status()
    
    # ==================== Message Operations ====================
    
    async def get_unread_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        resp = await self.client.get(f"{self.gateway_url}/internal/messages/unread/{agent_id}")
        resp.raise_for_status()
        return resp.json().get("messages", [])
    
    async def get_unread_count(self, agent_id: str) -> int:
        resp = await self.client.get(f"{self.gateway_url}/internal/messages/unread-count/{agent_id}")
        resp.raise_for_status()
        return resp.json().get("count", 0)
    
    async def mark_messages_read(self, message_ids: List[str]):
        if message_ids:
            resp = await self.client.patch(
                f"{self.gateway_url}/internal/messages/mark-read",
                json={"message_ids": message_ids}
            )
            resp.raise_for_status()
    
    async def mark_messages_processed(self, message_ids: List[str]):
        if message_ids:
            resp = await self.client.patch(
                f"{self.gateway_url}/internal/messages/mark-processed",
                json={"message_ids": message_ids}
            )
            resp.raise_for_status()
    
    # ==================== Agent Operations ====================
    
    async def get_setup_complete_agents(self) -> List[str]:
        resp = await self.client.get(f"{self.gateway_url}/internal/agents/setup-complete")
        resp.raise_for_status()
        return resp.json().get("agent_ids", [])
    
    async def set_agent_awake(self, agent_id: str):
        resp = await self.client.post(f"{self.gateway_url}/internal/agents/{agent_id}/awake")
        resp.raise_for_status()
    
    async def set_agent_sleep(self, agent_id: str, reason: str = "Task completed"):
        resp = await self.client.post(
            f"{self.gateway_url}/internal/agents/{agent_id}/sleep",
            json={"reason": reason}
        )
        resp.raise_for_status()
    
    async def get_agent_config(self, agent_id: str) -> Dict[str, Any]:
        resp = await self.client.get(f"{self.gateway_url}/internal/config/agent/{agent_id}")
        resp.raise_for_status()
        return resp.json()
    
    # ==================== LLM Operations ====================
    
    async def compact_context(self, agent_id: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compact context using LLM.
        
        Returns:
            {
                "success": bool,
                "summary": str,  # LLM-generated summary
                "compacted_count": int,
                "error": str (if failed)
            }
        """
        resp = await self.client.post(
            f"{self.gateway_url}/internal/llm/compact-context",
            json={"agent_id": agent_id, "messages": messages},
            timeout=120.0,  # Longer timeout for LLM call
        )
        resp.raise_for_status()
        return resp.json()
    
    # ==================== MCP Operations ====================
    
    async def create_agent_shared_mcp(self, agent_id: str, agent_index: int = 0):
        base = self.mcp_gateway_url
        resp = await self.client.post(
            f"{base}/internal/mcp/agent-shared",
            json={"agent_id": agent_id, "agent_index": agent_index}
        )
        resp.raise_for_status()
    
    async def has_agent_shared_mcp(self, agent_id: str) -> bool:
        base = self.mcp_gateway_url
        resp = await self.client.get(f"{base}/internal/mcp/agent-shared/{agent_id}/exists")
        resp.raise_for_status()
        return resp.json().get("exists", False)
    
    async def create_runtime_mcp(self, agent_id: str, subagent_id: str, agent_index: int = 0):
        base = self.mcp_gateway_url
        resp = await self.client.post(
            f"{base}/internal/mcp/runtime",
            json={"agent_id": agent_id, "subagent_id": subagent_id, "agent_index": agent_index}
        )
        resp.raise_for_status()
    
    async def remove_runtime_mcp(self, subagent_id: str):
        base = self.mcp_gateway_url
        resp = await self.client.delete(f"{base}/internal/mcp/runtime/{subagent_id}")
        resp.raise_for_status()
    
    async def create_aggregate_mcp(self, agent_id: str, subagent_id: str, agent_index: int = 0) -> str:
        base = self.mcp_gateway_url
        resp = await self.client.post(
            f"{base}/internal/mcp/aggregate",
            json={"agent_id": agent_id, "subagent_id": subagent_id, "agent_index": agent_index}
        )
        resp.raise_for_status()
        return resp.json().get("mcp_url", "")
    
    async def remove_aggregate_mcp(self, subagent_id: str):
        base = self.mcp_gateway_url
        resp = await self.client.delete(f"{base}/internal/mcp/aggregate/{subagent_id}")
        resp.raise_for_status()
    
    async def has_aggregate_mcp(self, subagent_id: str) -> bool:
        base = self.mcp_gateway_url
        resp = await self.client.get(f"{base}/internal/mcp/aggregate/{subagent_id}/exists")
        resp.raise_for_status()
        return resp.json().get("exists", False)
    
    # ==================== SSE Broadcast ====================
    
    async def broadcast_new_task(self, task_id: str, task_type: str, agent_id: str):
        try:
            resp = await self.client.post(
                f"{self.gateway_url}/internal/broadcast/new-task",
                json={"task_id": task_id, "task_type": task_type, "agent_id": agent_id}
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"[GatewayClient] Failed to broadcast: {e}")


class Master:
    """
    Core scheduler that orchestrates the entire system.
    
    v2.10: Runs as separate service, calls Gateway via HTTP.
    
    Components:
    - Monitor: Watches inbox, creates new Runtimes
    - Scheduler: Drives Rounds for each Runtime
    """
    
    def __init__(
        self,
        gateway_url: str,
        config: Optional[MasterConfig] = None,
        mcp_gateway_url: Optional[str] = None,
    ):
        """
        Initialize Master.
        
        Args:
            gateway_url: Backend (Gateway) HTTP URL (e.g. http://127.0.0.1:19999)
            config: Optional configuration
            mcp_gateway_url: MCP Gateway URL (e.g. http://127.0.0.1:19998). If None, uses gateway_url.
        """
        self.gateway_url = gateway_url
        self.mcp_gateway_url = mcp_gateway_url or gateway_url
        self.config = config or MasterConfig()
        
        # HTTP client for Backend + MCP Gateway
        self.gateway = GatewayClient(gateway_url, mcp_gateway_url=mcp_gateway_url)
        
        # Initialize components (lazy - they reference self)
        from .monitor import Monitor
        from .scheduler import Scheduler
        self.monitor = Monitor(self)
        self.scheduler = Scheduler(self)
        
        self._running = False
    
    async def start(self):
        """Start the Master."""
        if self._running:
            return
        
        self._running = True
        print("[Master] Starting...")
        
        # Start HTTP client
        await self.gateway.start()
        
        # Wait for Gateway to be ready
        await self._wait_for_gateway()
        
        # Recover any interrupted runtimes
        await self._recover_runtimes()
        
        # Start components
        await self.monitor.start()
        await self.scheduler.start()
        
        print("[Master] Started")
    
    async def stop(self):
        """Stop the Master."""
        if not self._running:
            return
        
        print("[Master] Stopping...")
        
        # Stop components
        await self.scheduler.stop()
        await self.monitor.stop()
        
        # Stop HTTP client
        await self.gateway.stop()
        
        self._running = False
        print("[Master] Stopped")
    
    async def _wait_for_gateway(self, timeout: int = 30):
        """Wait for Gateway to be ready."""
        print(f"[Master] Waiting for Gateway at {self.gateway_url}...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = await self.gateway.client.get(f"{self.gateway_url}/api/health")
                if resp.status_code == 200:
                    print("[Master] Gateway is ready")
                    return
            except Exception:
                pass
            await asyncio.sleep(1)
        raise RuntimeError(f"Gateway not ready after {timeout}s")
    
    async def _recover_runtimes(self):
        """Recover interrupted runtimes after restart."""
        runtimes = await self.gateway.get_active_runtimes()
        if not runtimes:
            print("[Master] No active runtimes to recover")
            return
        
        print(f"[Master] Recovering {len(runtimes)} active runtimes")
        
        # Group by agent_id
        agent_runtimes: dict = {}
        for runtime in runtimes:
            agent_id = runtime["agent_id"]
            if agent_id not in agent_runtimes:
                agent_runtimes[agent_id] = []
            agent_runtimes[agent_id].append(runtime)
        
        for agent_id, runtime_list in agent_runtimes.items():
            # Get agent_index
            try:
                agent_config = await self.gateway.get_agent_config(agent_id)
                agent_index = agent_config.get("agent_index", 0)
            except Exception:
                agent_index = 0
            
            for runtime in runtime_list:
                subagent_id = runtime["subagent_id"]
                print(f"  - Recovering {subagent_id}: {runtime['phase']}")
                await self._create_runtime_mcp_server(agent_id, subagent_id, agent_index)
        
        print(f"[Master] Recovery complete: {len(runtimes)} runtimes restored")
    
    # ========================================
    # Runtime Management
    # ========================================
    
    async def create_main_runtime(self, agent_id: str, agent_index: int = 0):
        """Create a new Main Runtime for an agent."""
        # Set agent to awake
        await self.set_agent_awake(agent_id)
        
        # Create runtime record
        runtime = await self.gateway.create_main_runtime(agent_id)
        subagent_id = runtime["subagent_id"]
        
        # Create MCP servers
        await self._create_runtime_mcp_server(agent_id, subagent_id, agent_index)
        
        print(f"[Master] Created Main Runtime {subagent_id} for agent {agent_id}")
        return runtime
    
    async def create_sub_runtime(
        self, 
        agent_id: str, 
        parent_subagent_id: str,
        initial_task: Optional[str] = None,
        share_context: bool = False,
        initial_context: Optional[List[Dict[str, Any]]] = None,
        agent_index: int = 0,
    ):
        """Create a new SubAgent Runtime."""
        context = initial_context or []
        
        # If sharing context, copy from parent
        if share_context and not initial_context:
            parent = await self.gateway.get_runtime(parent_subagent_id)
            if parent:
                context = list(parent.get("context", []))
        
        # Add initial task as user message
        if initial_task:
            context.append({
                "role": "user",
                "content": f"[SubAgent Task] {initial_task}",
            })
        
        # Create runtime record
        runtime = await self.gateway.create_sub_runtime(agent_id, parent_subagent_id, context)
        subagent_id = runtime["subagent_id"]
        
        # Create MCP servers
        await self._create_runtime_mcp_server(agent_id, subagent_id, agent_index)
        
        print(f"[Master] Created Sub Runtime {subagent_id} (parent: {parent_subagent_id})")
        return runtime
    
    async def destroy_runtime(self, subagent_id: str):
        """Destroy a Runtime and clean up its MCP Server."""
        runtime = await self.gateway.get_runtime(subagent_id)
        if not runtime:
            print(f"[Master] Runtime {subagent_id} not found for destruction")
            return
        
        # Remove MCP servers
        await self._remove_runtime_mcp_server(runtime["agent_id"], subagent_id)
        
        # Delete runtime record
        await self.gateway.delete_runtime(subagent_id)
        
        print(f"[Master] Destroyed Runtime {subagent_id}")
    
    # ========================================
    # MCP Server Management
    # ========================================
    
    async def _create_runtime_mcp_server(self, agent_id: str, subagent_id: str, agent_index: int = 0):
        """Create Agent shared layer, RuntimeMCP, and AggregateMCP via Gateway."""
        try:
            # Step 1: Create Agent shared layer MCP (if not exists)
            if not await self.gateway.has_agent_shared_mcp(agent_id):
                await self.gateway.create_agent_shared_mcp(agent_id, agent_index)
                print(f"[Master] Created shared MCP servers for agent {agent_id}")
            
            # Step 2: Create RuntimeMCP
            await self.gateway.create_runtime_mcp(agent_id, subagent_id, agent_index)
            print(f"[Master] Created RuntimeMCP for {subagent_id}")
            
            # Step 3: Create AggregateMCP
            mcp_url = await self.gateway.create_aggregate_mcp(agent_id, subagent_id, agent_index)
            
            # Store MCP URL in runtime record
            await self.gateway.update_runtime(subagent_id, mcp_url=mcp_url)
            
            print(f"[Master] Created Aggregate Gateway for {subagent_id} at {mcp_url}")
        except Exception as e:
            print(f"[Master] Error creating MCP servers for {subagent_id}: {e}")
            import traceback
            traceback.print_exc()
    
    async def _remove_runtime_mcp_server(self, agent_id: str, subagent_id: str):
        """Remove RuntimeMCP and AggregateMCP via Gateway."""
        try:
            await self.gateway.remove_aggregate_mcp(subagent_id)
            print(f"[Master] Removed AggregateMCP for {subagent_id}")
            
            await self.gateway.remove_runtime_mcp(subagent_id)
            print(f"[Master] Removed RuntimeMCP for {subagent_id}")
        except Exception as e:
            print(f"[Master] Error removing MCP servers for {subagent_id}: {e}")
    
    # ========================================
    # Wait for Runtime
    # ========================================
    
    async def wait_runtime_complete(
        self, 
        subagent_id: str, 
        timeout_seconds: int = 1800,
        poll_interval: float = 0.5
    ) -> Dict[str, Any]:
        """Synchronously wait for a Runtime to complete."""
        start_time = time.time()
        
        print(f"[Master] Waiting for runtime {subagent_id} to complete (timeout: {timeout_seconds}s)")
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed >= timeout_seconds:
                print(f"[Master] Runtime {subagent_id} timed out after {elapsed:.1f}s")
                await self.gateway.update_runtime(
                    subagent_id, 
                    status="failed", 
                    error=f"Timeout after {timeout_seconds}s"
                )
                await self.destroy_runtime(subagent_id)
                return {
                    "success": False,
                    "error": f"SubAgent timed out after {timeout_seconds} seconds",
                    "duration_seconds": elapsed,
                }
            
            runtime = await self.gateway.get_runtime(subagent_id)
            
            if not runtime:
                return {
                    "success": False,
                    "error": "Runtime not found (possibly deleted)",
                    "duration_seconds": elapsed,
                }
            
            if runtime["status"] == 'completed':
                result = self._extract_final_result(runtime)
                await self.destroy_runtime(subagent_id)
                print(f"[Master] Runtime {subagent_id} completed in {elapsed:.1f}s")
                return {
                    "success": True,
                    "result": result,
                    "duration_seconds": elapsed,
                }
            
            if runtime["status"] == 'failed':
                error = runtime.get("error") or "Unknown error"
                await self.destroy_runtime(subagent_id)
                print(f"[Master] Runtime {subagent_id} failed: {error}")
                return {
                    "success": False,
                    "error": error,
                    "duration_seconds": elapsed,
                }
            
            await asyncio.sleep(poll_interval)
            if elapsed > 60 and poll_interval < 2.0:
                poll_interval = min(poll_interval * 1.5, 2.0)
    
    def _extract_final_result(self, runtime: Dict[str, Any]) -> str:
        """Extract the final result from a completed runtime's context."""
        context = runtime.get("context", [])
        for msg in reversed(context):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if content and not msg.get("tool_calls"):
                    return content
        if context:
            return context[-1].get("content", "Task completed")
        return "Task completed"
    
    # ========================================
    # Agent State Management
    # ========================================
    
    async def set_agent_awake(self, agent_id: str):
        """Set agent state to awake."""
        await self.gateway.set_agent_awake(agent_id)
        print(f"[Master] Agent {agent_id} is now AWAKE")
    
    async def set_agent_sleep(self, agent_id: str):
        """Set agent state to sleep."""
        await self.gateway.set_agent_sleep(agent_id)
        print(f"[Master] Agent {agent_id} is now SLEEP")
    
    # ========================================
    # SSE Broadcasting
    # ========================================
    
    async def broadcast_new_task(self, task_id: str, task_type: str, agent_id: str):
        """Broadcast new task event to Workers via Gateway."""
        await self.gateway.broadcast_new_task(task_id, task_type, agent_id)
        print(f"[Master] Broadcast new_task: {task_id} ({task_type})")


# Global master instance
_master: Optional[Master] = None


def get_master() -> Optional[Master]:
    """Get the global Master instance."""
    return _master


def set_master(master: Master):
    """Set the global Master instance."""
    global _master
    _master = master
