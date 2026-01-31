"""
Monitor Component

Background task that monitors inbox for unread messages.
When a SLEEP agent has unread messages and no Main Runtime,
creates a new Main Runtime to start processing.
"""

import asyncio
from typing import TYPE_CHECKING, List, Set

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
        db = self.master.db
        
        # Get all agents
        async with db.get_connection() as conn:
            cursor = await conn.execute("SELECT id FROM agents WHERE setup_complete = 1")
            agents = await cursor.fetchall()
        
        for (agent_id,) in agents:
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
        db = self.master.db
        runtime_repo = self.master.runtime_repo
        
        # Check if agent has unread messages
        async with db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM chat_messages 
                WHERE agent_id = ? AND read = 0 AND processed = 0
            """, (agent_id,))
            (unread_count,) = await cursor.fetchone()
        
        if unread_count == 0:
            return  # No unread messages
        
        # Get Main Runtime (any status)
        main_runtime = await runtime_repo.get_main_runtime(agent_id)
        
        if main_runtime:
            if main_runtime.status == 'active':
                return  # Already running, scheduler will pick up messages
            
            if main_runtime.status == 'failed':
                # v2.9: Failed Runtime - delete and create new one
                print(f"[Monitor] Agent {agent_id} has failed Main Runtime {main_runtime.subagent_id}, deleting and recreating")
                await self.master.destroy_runtime(main_runtime.subagent_id)
                await self.master.create_main_runtime(agent_id)
            else:
                # Main Runtime exists but is sleeping/completed - wake it up
                print(f"[Monitor] Agent {agent_id} has {unread_count} unread messages, waking Main Runtime {main_runtime.subagent_id}")
                await runtime_repo.wake_main_runtime(main_runtime.subagent_id)
                
                # v2.9: Recreate MCP servers (they were destroyed or Gateway restarted)
                await self._ensure_runtime_mcp(agent_id, main_runtime.subagent_id)
                
                await self.master.set_agent_awake(agent_id)
        else:
            # No Main Runtime exists - create one (first time)
            print(f"[Monitor] Agent {agent_id} has {unread_count} unread messages, creating Main Runtime")
            await self.master.create_main_runtime(agent_id)
    
    async def _ensure_runtime_mcp(self, agent_id: str, subagent_id: str):
        """Ensure MCP servers exist for a Runtime (create if missing).
        
        Called when waking a Runtime after Gateway restart.
        """
        from mcp_servers.manager import get_mcp_manager
        from config.agents import get_agent_config_manager
        
        mcp_mgr = get_mcp_manager()
        if not mcp_mgr:
            print(f"[Monitor] Warning: MCPManager not available")
            return
        
        # Check if Aggregate MCP already exists
        if mcp_mgr.get_aggregate_gateway(subagent_id):
            return  # Already exists
        
        # Get agent_index for port allocation
        agent_mgr = get_agent_config_manager()
        agent = agent_mgr.get_agent(agent_id)
        agent_index = agent.vm.agent_index if agent else 0
        
        print(f"[Monitor] Recreating MCP servers for {subagent_id}")
        await self.master._create_runtime_mcp_server(agent_id, subagent_id, agent_index)
