"""
Master - Core Scheduler

The central orchestrator for the multi-process architecture.
Manages Agent Runtimes, drives Rounds, and coordinates Workers.

v2.5: Added wait_runtime_complete for SubAgent synchronous execution
v2.6: Added MCP Server three-layer architecture management
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .monitor import Monitor
from .scheduler import Scheduler


@dataclass
class MasterConfig:
    """Configuration for Master."""
    monitor_interval: float = 1.0  # seconds
    scheduler_interval: float = 0.1  # seconds
    max_rounds_per_runtime: int = 50


class Master:
    """
    Core scheduler that orchestrates the entire system.
    
    Components:
    - Monitor: Watches inbox, creates new Runtimes
    - Scheduler: Drives Rounds for each Runtime
    
    Responsibilities:
    - Create and manage Agent Runtimes
    - Prepare context for Workers
    - Create and track action tasks
    - Broadcast SSE events to Workers
    - Collect results and advance Rounds
    """
    
    def __init__(self, db, sse_broadcaster, config: Optional[MasterConfig] = None):
        """
        Initialize Master.
        
        Args:
            db: Database instance
            sse_broadcaster: SSE broadcaster for sending events to Workers
            config: Optional configuration
        """
        self.db = db
        self.sse_broadcaster = sse_broadcaster
        self.config = config or MasterConfig()
        
        # Initialize repositories
        from db.repositories import RuntimeRepository, AgentStateRepository
        self.runtime_repo = RuntimeRepository(db)
        self.agent_state_repo = AgentStateRepository(db)
        
        # Initialize components
        self.monitor = Monitor(self)
        self.scheduler = Scheduler(self)
        
        self._running = False
    
    async def start(self):
        """Start the Master."""
        if self._running:
            return
        
        self._running = True
        print("[Master] Starting...")
        
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
        
        self._running = False
        print("[Master] Stopped")
    
    async def _recover_runtimes(self):
        """
        Recover interrupted runtimes after restart.
        
        Since MCP Servers are stateless, we simply recreate:
        1. Agent Gateway (聚合层) - if not exists
        2. Runtime MCP Server - for each active runtime
        
        Monitor/Scheduler will automatically continue processing
        tasks from the database.
        """
        from config.agents import get_agent_config_manager
        
        runtimes = await self.runtime_repo.get_all_active_runtimes()
        if not runtimes:
            print("[Master] No active runtimes to recover")
            return
        
        print(f"[Master] Recovering {len(runtimes)} active runtimes")
        
        # Group runtimes by agent_id to avoid duplicate gateway creation
        agent_runtimes: dict = {}
        for runtime in runtimes:
            if runtime.agent_id not in agent_runtimes:
                agent_runtimes[runtime.agent_id] = []
            agent_runtimes[runtime.agent_id].append(runtime)
        
        # Get agent config manager for agent_index lookup
        agent_mgr = get_agent_config_manager()
        
        for agent_id, agent_runtime_list in agent_runtimes.items():
            # Get agent_index from config (default to 0 if not found)
            agent = agent_mgr.get_agent(agent_id)
            agent_index = agent.vm.agent_index if agent else 0
            
            # v2.7: Create Runtime MCP Server + Aggregate Gateway for each active runtime
            for runtime in agent_runtime_list:
                print(f"  - Recovering {runtime.subagent_id}: {runtime.phase}")
                await self._create_runtime_mcp_server(agent_id, runtime.subagent_id, agent_index)
        
        print(f"[Master] Recovery complete: {len(runtimes)} runtimes restored")
    
    # ========================================
    # Runtime Management
    # ========================================
    
    async def create_main_runtime(self, agent_id: str, agent_index: int = 0):
        """
        Create a new Main Runtime for an agent.
        
        v2.7: Creates Runtime MCP Server + Aggregate Gateway
        
        Args:
            agent_id: Agent ID
            agent_index: Agent index for port allocation
        
        Returns:
            The created AgentRuntime
        """
        # Set agent to awake
        await self.set_agent_awake(agent_id)
        
        # Create runtime record
        runtime = await self.runtime_repo.create_main_runtime(agent_id)
        
        # v2.7: Create Runtime MCP Server + Aggregate Gateway
        await self._create_runtime_mcp_server(agent_id, runtime.subagent_id, agent_index)
        
        print(f"[Master] Created Main Runtime {runtime.subagent_id} for agent {agent_id}")
        
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
        """
        Create a new SubAgent Runtime.
        
        v2.6: Also creates Runtime-specific MCP Server.
        
        Args:
            agent_id: VM Agent ID
            parent_subagent_id: Parent runtime's subagent_id
            initial_task: Task description for the SubAgent
            share_context: Whether to copy parent's context
            initial_context: Optional explicit initial context
            agent_index: Agent index for port allocation
        
        Returns:
            The created AgentRuntime
        """
        context = initial_context or []
        
        # If sharing context, copy from parent
        if share_context and not initial_context:
            parent = await self.runtime_repo.get_by_id(parent_subagent_id)
            if parent:
                context = list(parent.context)  # Copy parent's context
        
        # Add initial task as a system/user message
        if initial_task:
            context.append({
                "role": "user",
                "content": f"[SubAgent Task] {initial_task}",
            })
        
        # Create runtime record
        runtime = await self.runtime_repo.create_sub_runtime(
            agent_id, parent_subagent_id, context
        )
        
        # v2.6: Create Runtime-specific MCP Server
        await self._create_runtime_mcp_server(agent_id, runtime.subagent_id, agent_index)
        
        print(f"[Master] Created Sub Runtime {runtime.subagent_id} (parent: {parent_subagent_id})")
        
        return runtime
    
    async def destroy_runtime(self, subagent_id: str):
        """
        Destroy a Runtime and clean up its MCP Server.
        
        v2.6: Also removes Runtime-specific MCP Server.
        
        Args:
            subagent_id: Runtime ID to destroy
        """
        runtime = await self.runtime_repo.get_by_id(subagent_id)
        if not runtime:
            print(f"[Master] Runtime {subagent_id} not found for destruction")
            return
        
        # v2.6: Remove Runtime-specific MCP Server
        await self._remove_runtime_mcp_server(runtime.agent_id, subagent_id)
        
        # Delete runtime record
        await self.runtime_repo.delete(subagent_id)
        
        print(f"[Master] Destroyed Runtime {subagent_id}")
    
    # ========================================
    # MCP Server Management (v2.9)
    # ========================================
    
    async def _create_runtime_mcp_server(self, agent_id: str, subagent_id: str, agent_index: int = 0):
        """
        Create Agent shared layer, RuntimeMCP, and AggregateMCP.
        
        v2.9: 三步创建：
        1. 创建 Agent 共享层 MCP (chat, memory, local, qemudebug) - 如果不存在
        2. 创建 RuntimeMCP (runtime_* 工具)
        3. 创建 AggregateMCP (聚合所有工具)
        
        存储 AggregateMCP 的 URL 到 runtime 记录，Worker 从这里加载工具。
        """
        from mcp_servers.manager import get_mcp_manager
        
        mcp_mgr = get_mcp_manager()
        if not mcp_mgr:
            print(f"[Master] Warning: MCPManager not available")
            return
        
        try:
            # Step 1: 创建 Agent 共享层 MCP (如果不存在)
            if not mcp_mgr.has_agent_shared_servers(agent_id):
                await mcp_mgr.create_agent_shared_servers(
                    agent_id=agent_id,
                    agent_index=agent_index,
                )
                print(f"[Master] Created shared MCP servers for agent {agent_id}")
            
            # Step 2: 创建 RuntimeMCP (runtime_* 工具)
            await mcp_mgr.create_runtime_server(
                agent_id=agent_id,
                subagent_id=subagent_id,
                agent_index=agent_index,
            )
            print(f"[Master] Created RuntimeMCP for {subagent_id}")
            
            # Step 3: 创建 AggregateMCP (聚合所有工具)
            await mcp_mgr.create_aggregate_gateway(
                agent_id=agent_id,
                subagent_id=subagent_id,
                agent_index=agent_index,
            )
            
            # 存储 AggregateMCP 的 URL（Worker 从这里加载工具）
            mcp_url = mcp_mgr.get_aggregate_mount_path(subagent_id)
            await self.runtime_repo.set_mcp_url(subagent_id, mcp_url)
            
            print(f"[Master] Created Aggregate Gateway for {subagent_id} at {mcp_url}")
        except Exception as e:
            print(f"[Master] Error creating MCP servers for {subagent_id}: {e}")
            import traceback
            traceback.print_exc()
    
    async def _remove_runtime_mcp_server(self, agent_id: str, subagent_id: str):
        """
        Remove RuntimeMCP and AggregateMCP.
        
        v2.8: 两步移除：
        1. 移除 AggregateMCP
        2. 移除 RuntimeMCP
        """
        from mcp_servers.manager import get_mcp_manager
        
        mcp_mgr = get_mcp_manager()
        if not mcp_mgr:
            print(f"[Master] Warning: MCPManager not available")
            return
        
        try:
            # Step 1: 移除 AggregateMCP
            await mcp_mgr.remove_aggregate_gateway(subagent_id)
            print(f"[Master] Removed AggregateMCP for {subagent_id}")
            
            # Step 2: 移除 RuntimeMCP
            await mcp_mgr.remove_runtime_server(subagent_id)
            print(f"[Master] Removed RuntimeMCP for {subagent_id}")
        except Exception as e:
            print(f"[Master] Error removing Runtime MCP Server for {subagent_id}: {e}")
    
    async def wait_runtime_complete(
        self, 
        subagent_id: str, 
        timeout_seconds: int = 1800,
        poll_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Synchronously wait for a Runtime to complete.
        
        Used by context_call MCP tool for SubAgent execution.
        
        Args:
            subagent_id: Runtime ID to wait for
            timeout_seconds: Maximum wait time (default 30 minutes)
            poll_interval: Polling interval in seconds
        
        Returns:
            {"success": bool, "result": str, "error": str, "duration_seconds": float}
        """
        start_time = time.time()
        
        print(f"[Master] Waiting for runtime {subagent_id} to complete (timeout: {timeout_seconds}s)")
        
        while True:
            elapsed = time.time() - start_time
            
            # Check timeout
            if elapsed >= timeout_seconds:
                print(f"[Master] Runtime {subagent_id} timed out after {elapsed:.1f}s")
                # Mark as failed
                await self.runtime_repo.mark_failed(subagent_id, f"Timeout after {timeout_seconds}s")
                # v2.6: Destroy Runtime (includes MCP Server cleanup)
                await self.destroy_runtime(subagent_id)
                return {
                    "success": False,
                    "error": f"SubAgent timed out after {timeout_seconds} seconds",
                    "duration_seconds": elapsed,
                }
            
            # Get runtime status
            runtime = await self.runtime_repo.get_by_id(subagent_id)
            
            if not runtime:
                # Runtime was deleted (shouldn't happen normally)
                return {
                    "success": False,
                    "error": "Runtime not found (possibly deleted)",
                    "duration_seconds": elapsed,
                }
            
            if runtime.status == 'completed':
                # Extract result from context (last assistant message)
                result = self._extract_final_result(runtime)
                
                # v2.6: Destroy Runtime (includes MCP Server cleanup)
                await self.destroy_runtime(subagent_id)
                
                print(f"[Master] Runtime {subagent_id} completed in {elapsed:.1f}s")
                return {
                    "success": True,
                    "result": result,
                    "duration_seconds": elapsed,
                }
            
            if runtime.status == 'failed':
                error = runtime.error or "Unknown error"
                
                # v2.6: Destroy Runtime (includes MCP Server cleanup)
                await self.destroy_runtime(subagent_id)
                
                print(f"[Master] Runtime {subagent_id} failed: {error}")
                return {
                    "success": False,
                    "error": error,
                    "duration_seconds": elapsed,
                }
            
            # Still active, wait and poll again
            await asyncio.sleep(poll_interval)
            
            # Increase poll interval over time (up to 2 seconds)
            if elapsed > 60 and poll_interval < 2.0:
                poll_interval = min(poll_interval * 1.5, 2.0)
    
    def _extract_final_result(self, runtime) -> str:
        """Extract the final result from a completed runtime's context."""
        # Look for the last assistant message that looks like a final response
        for msg in reversed(runtime.context):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                # Skip tool calls, look for actual content
                if content and not msg.get("tool_calls"):
                    return content
        
        # Fallback: return last message content
        if runtime.context:
            return runtime.context[-1].get("content", "Task completed")
        
        return "Task completed"
    
    # ========================================
    # Agent State Management
    # ========================================
    
    async def set_agent_awake(self, agent_id: str):
        """Set agent state to awake."""
        await self.agent_state_repo.set_awake(agent_id)
        print(f"[Master] Agent {agent_id} is now AWAKE")
    
    async def set_agent_sleep(self, agent_id: str):
        """Set agent state to sleep."""
        await self.agent_state_repo.set_sleep(agent_id, reason="Task completed")
        print(f"[Master] Agent {agent_id} is now SLEEP")
    
    # ========================================
    # SSE Broadcasting
    # ========================================
    
    async def broadcast_new_task(self, task_id: str, task_type: str, agent_id: str):
        """Broadcast new task event to Workers."""
        if self.sse_broadcaster:
            # Use the broadcaster's helper method which formats data correctly
            await self.sse_broadcaster.broadcast_new_task(
                task_id=task_id,
                agent_id=agent_id,
                task_type=task_type,
            )
            print(f"[Master] Broadcast new_task: {task_id} ({task_type})")
    
    # ========================================
    # Task Result Handling
    # ========================================
    
    async def handle_task_result(self, task_id: str, result: Dict[str, Any]):
        """
        Handle result from a Worker.
        This is called by Gateway when Worker submits result.
        """
        # Get task info
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT subagent_id, type FROM action_tasks WHERE id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()
        
        if not row:
            print(f"[Master] Task {task_id} not found")
            return
        
        subagent_id, task_type = row
        
        # If this was a think task, process the actions
        if task_type == 'think':
            await self._process_think_result(subagent_id, result)
    
    async def _process_think_result(self, subagent_id: str, result: Dict[str, Any]):
        """Process result from a think task."""
        # This is handled by the scheduler when it checks waiting_actions
        # The scheduler will see the task is done and process the actions
        pass


# Global master instance (set by main.py)
_master: Optional[Master] = None


def get_master() -> Optional[Master]:
    """Get the global Master instance."""
    return _master


def set_master(master: Master):
    """Set the global Master instance."""
    global _master
    _master = master
