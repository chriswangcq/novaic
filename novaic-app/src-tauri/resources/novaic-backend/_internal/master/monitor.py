"""
Monitor Component (v14)

Background task that monitors inbox for unread messages.
When a sleeping SubAgent has unread messages that match wake triggers,
wakes the SubAgent and creates a new Runtime.

v14: SubAgent state refactor
- Polls from messages (not all agents)
- Uses SubAgent.status atomic wake
- Checks wake_triggers for message matching
- Shorter polling interval (0.2s)
"""

import re
import asyncio
from typing import TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from .master import Master


class Monitor:
    """Monitors inbox and triggers SubAgent wake + Runtime creation."""
    
    def __init__(self, master: 'Master'):
        self.master = master
        self.running = False
        self.check_interval = 0.2  # v14: Shorter interval for faster response
        self._task = None
    
    async def start(self):
        """Start the monitor loop."""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run())
        print("[Monitor] Started (v14)")
    
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
                await self._check_unread_messages()
            except Exception as e:
                print(f"[Monitor] Error in check loop: {e}")
                import traceback
                traceback.print_exc()
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_unread_messages(self):
        """Check unread messages and wake SubAgents as needed."""
        gateway = self.master.gateway
        
        # Get unread messages grouped by agent
        unread_by_agent = await gateway.get_unread_messages_grouped_by_agent()
        
        for agent_id, messages in unread_by_agent.items():
            try:
                await self._check_agent(agent_id, messages)
            except Exception as e:
                print(f"[Monitor] Error checking agent {agent_id}: {e}")
    
    async def _check_agent(self, agent_id: str, messages: List[Dict[str, Any]]):
        """Check a single agent for potential wake.
        
        v14 Logic:
        1. Get main SubAgent
        2. If summarizing: skip (not ready for new work)
        3. If awake: skip (already has active runtime)
        4. If sleeping: check wake_triggers
        5. If triggers match: atomic wake -> create runtime
        """
        gateway = self.master.gateway
        
        # Get or create main SubAgent
        subagent = await gateway.get_main_subagent(agent_id)
        if not subagent:
            print(f"[Monitor] Could not get/create main SubAgent for {agent_id}")
            return
        
        # Check SubAgent status
        status = subagent.get("status", "sleeping")
        
        if status == "summarizing":
            # SubAgent is processing summary, cannot wake yet
            return
        
        if status == "awake":
            # SubAgent already has active runtime
            # The runtime will pick up new messages in next think round
            return
        
        # status == "sleeping" - check if we should wake
        wake_triggers = subagent.get("wake_triggers", [{"type": "user_response"}])
        
        if not self._should_wake(wake_triggers, messages):
            return
        
        # Try to wake SubAgent (atomic CAS operation)
        subagent_id = subagent.get("subagent_id", "main")
        woken = await gateway.try_wake_subagent(agent_id, subagent_id)
        
        if woken:
            print(f"[Monitor] Woke SubAgent {subagent_id} for agent {agent_id}")
            # Create new runtime for this SubAgent
            await self.master.create_runtime(agent_id, subagent_id)
        else:
            # Another Monitor/process already woke it, skip
            print(f"[Monitor] SubAgent {subagent_id} already woken (CAS conflict)")
    
    def _should_wake(
        self, 
        triggers: List[Dict[str, Any]], 
        messages: List[Dict[str, Any]]
    ) -> bool:
        """Check if messages match any wake trigger.
        
        Trigger types:
        - user_response: Any user message wakes
        - keyword: Message contains pattern
        - cron: Time-based (handled elsewhere)
        - timeout: Time-based (handled elsewhere)
        """
        for trigger in triggers:
            trigger_type = trigger.get("type")
            
            if trigger_type == "user_response":
                # Any user message triggers wake
                if any(m.get("type") == "USER_MESSAGE" for m in messages):
                    return True
            
            elif trigger_type == "keyword":
                # Check if any message contains the keyword pattern
                pattern = trigger.get("pattern", "")
                if pattern:
                    try:
                        regex = re.compile(pattern, re.IGNORECASE)
                        for m in messages:
                            content = m.get("content", "")
                            if regex.search(content):
                                return True
                    except re.error:
                        # Invalid regex, skip this trigger
                        pass
            
            # cron and timeout are handled by a separate scheduled task
            # (not implemented in this version)
        
        return False
