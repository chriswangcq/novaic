"""
Monitor Component

Background task that monitors inbox for unread messages.
When a SLEEP agent has unread messages and no Main Runtime,
creates a new Main Runtime to start processing.

v2.10: Uses Gateway HTTP API instead of direct DB access.
"""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .master import Master


class Monitor:
    """Monitors inbox and triggers Runtime creation."""
    
    def __init__(self, master: 'Master'):
        self.master = master
        self.running = False
        self.check_interval = 1.0  # seconds
        self._task = None
    
    async def start(self):
        """Start the monitor loop."""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run())
        print("[Monitor] Started")
    
    async def stop(self):
        """Stop the monitor loop."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("[Monitor] Stopped")
    
    async def _run(self):
        """Main monitor loop."""
        while self.running:
            try:
                await self._check_agents()
            except Exception as e:
                print(f"[Monitor] Error in check loop: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_agents(self):
        """Check all agents for unread messages."""
        gateway = self.master.gateway
        
        # Get all setup-complete agents
        agent_ids = await gateway.get_setup_complete_agents()
        
        for agent_id in agent_ids:
            await self._check_agent(agent_id)
    
    async def _check_agent(self, agent_id: str):
        """Check a single agent for unread messages.
        
        Logic:
        - If no unread messages: do nothing
        - If Main Runtime is active: do nothing (scheduler handles it)
        - If Main Runtime is failed: delete and create new one
        - If Main Runtime is sleeping/completed: wake it up + create MCP
        - If no Main Runtime exists: create one
        """
        gateway = self.master.gateway
        
        # Check if agent has unread messages
        unread_count = await gateway.get_unread_count(agent_id)
        
        if unread_count == 0:
            return  # No unread messages
        
        # Get Main Runtime (any status)
        main_runtime = await gateway.get_main_runtime(agent_id)
        
        if main_runtime:
            phase = main_runtime.get("phase")
            subagent_id = main_runtime.get("subagent_id")
            
            # Check if Scheduler is actively processing this runtime
            # Active phases: need_think, waiting_actions, waiting_actions_final
            active_phases = ['need_think', 'waiting_actions', 'waiting_actions_final']
            if phase in active_phases:
                return  # Already running, scheduler will pick up messages
            
            if phase == 'failed':
                # Failed Runtime - delete and create new one
                print(f"[Monitor] Agent {agent_id} has failed Main Runtime {subagent_id}, deleting and recreating")
                await self.master.destroy_runtime(subagent_id)
                await self.master.create_main_runtime(agent_id)
            else:
                # Main Runtime exists but is sleeping/completed - wake it up (atomic CAS)
                print(f"[Monitor] Agent {agent_id} has {unread_count} unread messages, waking Main Runtime {subagent_id}")
                woken = await gateway.wake_runtime(subagent_id)
                
                if woken:
                    # Successfully woken - recreate MCP servers
                    await self._ensure_runtime_mcp(agent_id, subagent_id)
                    await self.master.set_agent_awake(agent_id)
                    print(f"[Monitor] Successfully woke Runtime {subagent_id}")
                else:
                    # Already active (another Monitor got there first) - skip
                    print(f"[Monitor] Runtime {subagent_id} already active (CAS conflict), skipping")
        else:
            # No Main Runtime exists - create one (first time)
            print(f"[Monitor] Agent {agent_id} has {unread_count} unread messages, creating Main Runtime")
            await self.master.create_main_runtime(agent_id)
    
    async def _ensure_runtime_mcp(self, agent_id: str, subagent_id: str):
        """Ensure MCP servers exist for a Runtime (create if missing)."""
        gateway = self.master.gateway
        
        # Check if Aggregate MCP already exists
        if await gateway.has_aggregate_mcp(subagent_id):
            return  # Already exists
        
        # Get agent_index for port allocation
        try:
            agent_config = await gateway.get_agent_config(agent_id)
            agent_index = agent_config.get("agent_index", 0)
        except Exception:
            agent_index = 0
        
        print(f"[Monitor] Recreating MCP servers for {subagent_id}")
        await self.master._create_runtime_mcp_server(agent_id, subagent_id, agent_index)
