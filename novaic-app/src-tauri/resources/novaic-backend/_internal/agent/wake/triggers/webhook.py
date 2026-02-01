"""
WebhookTrigger - HTTP webhook-based wake trigger
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .base import BaseTrigger, TriggerConfig

logger = logging.getLogger(__name__)


@dataclass
class WebhookTriggerConfig(TriggerConfig):
    """Configuration for webhook triggers."""
    endpoint: str = ""  # Webhook endpoint path
    secret: Optional[str] = None  # Optional secret for verification
    wake_message_template: str = "Webhook triggered: {webhook_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **super().to_dict(),
            "type": "webhook",
            "endpoint": self.endpoint,
            "has_secret": self.secret is not None,
            "wake_message_template": self.wake_message_template,
        }


class WebhookTrigger(BaseTrigger):
    """
    Webhook-based wake trigger.
    
    Receives HTTP requests and converts them to wake events.
    The actual HTTP endpoint is handled by the WakeController's API.
    
    Features:
    - Optional secret-based verification
    - Customizable wake message template
    - Request data forwarding
    """
    
    def __init__(self, config: WebhookTriggerConfig):
        """
        Initialize the webhook trigger.
        
        Args:
            config: Webhook trigger configuration
        """
        super().__init__(config)
        self.webhook_config = config
        self._last_fire: Optional[datetime] = None
        self._fire_count = 0
    
    async def start(self) -> None:
        """Start the webhook trigger (registers it as active)."""
        self._running = True
        logger.info(f"[WebhookTrigger] Started: {self.name} (endpoint: {self.webhook_config.endpoint})")
    
    async def stop(self) -> None:
        """Stop the webhook trigger."""
        self._running = False
        logger.info(f"[WebhookTrigger] Stopped: {self.name}")
    
    def verify_secret(self, provided_secret: str) -> bool:
        """
        Verify the provided secret against the configured secret.
        
        Args:
            provided_secret: Secret from the incoming request
        
        Returns:
            True if secret matches or no secret is configured
        """
        if not self.webhook_config.secret:
            return True
        return provided_secret == self.webhook_config.secret
    
    async def handle_request(
        self,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Handle an incoming webhook request.
        
        Args:
            data: Request body data
            headers: Request headers
        
        Returns:
            Response data
        """
        if not self.enabled:
            return {"success": False, "error": "Webhook is disabled"}
        
        if not self._running:
            return {"success": False, "error": "Webhook is not running"}
        
        # Verify secret if configured
        if self.webhook_config.secret:
            secret = (headers or {}).get("X-Webhook-Secret", "")
            if not self.verify_secret(secret):
                logger.warning(f"[WebhookTrigger] Invalid secret for {self.name}")
                return {"success": False, "error": "Invalid secret"}
        
        # Fire the trigger
        self._fire_count += 1
        self._last_fire = datetime.now()
        
        # Build wake message
        message = self.webhook_config.wake_message_template.format(
            webhook_name=self.name,
            data=data,
        )
        
        logger.info(f"[WebhookTrigger] Fired: {self.name}")
        
        await self._fire(
            message=message,
            data={
                "webhook_data": data,
                "fire_time": self._last_fire.isoformat(),
                "fire_count": self._fire_count,
            }
        )
        
        return {
            "success": True,
            "trigger_id": self.id,
            "fire_count": self._fire_count,
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get trigger information."""
        info = self.webhook_config.to_dict()
        info.update({
            "is_running": self._running,
            "last_fire": self._last_fire.isoformat() if self._last_fire else None,
            "fire_count": self._fire_count,
        })
        return info
