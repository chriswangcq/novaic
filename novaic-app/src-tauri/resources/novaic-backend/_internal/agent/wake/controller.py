"""
WakeController - Manages wake triggers and agent wake-up

Central controller for all wake triggers. Coordinates trigger registration,
lifecycle management, and agent wake-up.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime

from .triggers.base import BaseTrigger, TriggerConfig
from .triggers.cron import CronTrigger, CronTriggerConfig
from .triggers.webhook import WebhookTrigger, WebhookTriggerConfig

logger = logging.getLogger(__name__)


@dataclass
class WakeContext:
    """Context for a wake-up request."""
    trigger_id: str
    trigger_name: str
    trigger_type: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime


class WakeController:
    """
    Central controller for wake triggers.
    
    Responsibilities:
    - Register and manage triggers
    - Route wake events via MessageRepository and WorkerBroadcaster (v11)
    - Persist trigger configurations
    - Provide API for trigger management
    """
    
    def __init__(
        self,
        storage_dir: str = "storage/triggers",
    ):
        """
        Initialize the wake controller.
        
        Args:
            storage_dir: Directory for trigger configuration persistence
        """
        self.storage_dir = storage_dir
        
        # Registered triggers
        self._triggers: Dict[str, BaseTrigger] = {}
        
        # Statistics
        self._stats = {
            "wakes_triggered": 0,
            "wakes_failed": 0,
        }
    
    async def add_cron_trigger(
        self,
        name: str,
        cron_expr: str,
        wake_message: str,
        enabled: bool = True,
        trigger_id: Optional[str] = None,
    ) -> str:
        """
        Add a cron-based wake trigger.
        
        Args:
            name: Trigger name
            cron_expr: Cron expression (e.g., "0 9 * * *")
            wake_message: Message to send when waking agent
            enabled: Whether trigger is enabled
            trigger_id: Optional specific ID
        
        Returns:
            Trigger ID
        """
        config = CronTriggerConfig(
            name=name,
            cron_expr=cron_expr,
            wake_message=wake_message,
            enabled=enabled,
        )
        if trigger_id:
            config.id = trigger_id
        
        trigger = CronTrigger(config)
        trigger.set_callback(self._on_trigger_fire)
        
        self._triggers[trigger.id] = trigger
        
        if enabled:
            await trigger.start()
        
        logger.info(f"[WakeController] Added cron trigger: {name} ({cron_expr})")
        return trigger.id
    
    async def add_webhook_trigger(
        self,
        name: str,
        endpoint: str,
        wake_message_template: str = "Webhook triggered: {webhook_name}",
        secret: Optional[str] = None,
        enabled: bool = True,
        trigger_id: Optional[str] = None,
    ) -> str:
        """
        Add a webhook-based wake trigger.
        
        Args:
            name: Trigger name
            endpoint: Webhook endpoint path
            wake_message_template: Message template
            secret: Optional secret for verification
            enabled: Whether trigger is enabled
            trigger_id: Optional specific ID
        
        Returns:
            Trigger ID
        """
        config = WebhookTriggerConfig(
            name=name,
            endpoint=endpoint,
            wake_message_template=wake_message_template,
            secret=secret,
            enabled=enabled,
        )
        if trigger_id:
            config.id = trigger_id
        
        trigger = WebhookTrigger(config)
        trigger.set_callback(self._on_trigger_fire)
        
        self._triggers[trigger.id] = trigger
        
        if enabled:
            await trigger.start()
        
        logger.info(f"[WakeController] Added webhook trigger: {name} ({endpoint})")
        return trigger.id
    
    async def remove_trigger(self, trigger_id: str) -> bool:
        """
        Remove a trigger.
        
        Args:
            trigger_id: ID of the trigger to remove
        
        Returns:
            True if trigger was found and removed
        """
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return False
        
        await trigger.stop()
        del self._triggers[trigger_id]
        
        logger.info(f"[WakeController] Removed trigger: {trigger_id}")
        return True
    
    async def enable_trigger(self, trigger_id: str) -> bool:
        """Enable a trigger."""
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return False
        
        trigger.enable()
        if not trigger.is_running:
            await trigger.start()
        
        return True
    
    async def disable_trigger(self, trigger_id: str) -> bool:
        """Disable a trigger."""
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return False
        
        trigger.disable()
        return True
    
    def get_trigger(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """Get trigger info by ID."""
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return None
        return trigger.get_info()
    
    def list_triggers(self) -> List[Dict[str, Any]]:
        """List all triggers."""
        return [trigger.get_info() for trigger in self._triggers.values()]
    
    async def handle_webhook(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Handle an incoming webhook request.
        
        Args:
            endpoint: The webhook endpoint path
            data: Request body
            headers: Request headers
        
        Returns:
            Response data
        """
        # Find trigger by endpoint
        for trigger in self._triggers.values():
            if isinstance(trigger, WebhookTrigger):
                if trigger.webhook_config.endpoint == endpoint:
                    return await trigger.handle_request(data, headers)
        
        return {"success": False, "error": f"No webhook trigger for endpoint: {endpoint}"}
    
    async def _on_trigger_fire(self, trigger_id: str, data: Dict[str, Any]) -> None:
        """
        Handle trigger fire event.
        
        v11: Updated to use new multi-process architecture.
        
        Args:
            trigger_id: ID of the fired trigger
            data: Trigger data including message
        """
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            logger.warning(f"[WakeController] Unknown trigger: {trigger_id}")
            return
        
        # Create wake context
        context = WakeContext(
            trigger_id=trigger_id,
            trigger_name=trigger.name,
            trigger_type=type(trigger).__name__,
            message=data.get("message", "Wake-up triggered"),
            data=data,
            timestamp=datetime.now(),
        )
        
        # v12: Store message in database - Monitor will detect and create Runtime
        try:
            from db.database import get_database
            from db.repositories.message import MessageRepository
            from main import get_current_agent_id
            
            agent_id = get_current_agent_id()
            if not agent_id:
                logger.warning("[WakeController] No current agent, cannot process wake trigger")
                self._stats["wakes_failed"] += 1
                return
            
            db = get_database()
            msg_repo = MessageRepository(db)
            
            # Determine message type based on trigger type
            msg_type = "CRON_TRIGGER" if context.trigger_type == "CronTrigger" else "WEBHOOK"
            if context.trigger_type not in ("CronTrigger", "WebhookTrigger"):
                msg_type = "SYSTEM_MESSAGE"
            
            # Store message in database - Monitor will detect and create Runtime
            msg = await msg_repo.add_message(
                agent_id=agent_id,
                type=msg_type,
                content=context.message,
                metadata={
                    "trigger_id": context.trigger_id,
                    "trigger_name": context.trigger_name,
                    "trigger_type": context.trigger_type,
                    "trigger_data": context.data,
                    "source": f"wake:{context.trigger_type.lower()}",
                },
            )
            
            # v12: No broadcast_new_message needed
            # Monitor polls for unread messages and creates Runtimes
            
            self._stats["wakes_triggered"] += 1
            logger.info(f"[WakeController] Wake message stored for trigger: {trigger.name}")
            
        except Exception as e:
            self._stats["wakes_failed"] += 1
            logger.error(f"[WakeController] Failed to process wake trigger: {e}")
    
    async def start(self) -> None:
        """Start all enabled triggers."""
        for trigger in self._triggers.values():
            if trigger.enabled and not trigger.is_running:
                try:
                    await trigger.start()
                except Exception as e:
                    logger.error(f"[WakeController] Failed to start trigger {trigger.id}: {e}")
        
        logger.info(f"[WakeController] Started {len(self._triggers)} triggers")
    
    async def stop(self) -> None:
        """Stop all triggers."""
        for trigger in self._triggers.values():
            try:
                await trigger.stop()
            except Exception as e:
                logger.error(f"[WakeController] Failed to stop trigger {trigger.id}: {e}")
        
        logger.info("[WakeController] Stopped all triggers")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get controller statistics."""
        return {
            **self._stats,
            "total_triggers": len(self._triggers),
            "enabled_triggers": sum(1 for t in self._triggers.values() if t.enabled),
            "running_triggers": sum(1 for t in self._triggers.values() if t.is_running),
        }
