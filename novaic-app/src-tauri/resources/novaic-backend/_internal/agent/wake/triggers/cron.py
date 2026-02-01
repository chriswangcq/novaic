"""
CronTrigger - Time-based wake trigger using cron expressions
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .base import BaseTrigger, TriggerConfig

logger = logging.getLogger(__name__)

# Try to import APScheduler, fall back to simple implementation if not available
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger as APSCronTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    logger.warning("[CronTrigger] APScheduler not available, using simple implementation")


@dataclass
class CronTriggerConfig(TriggerConfig):
    """Configuration for cron triggers."""
    cron_expr: str = "0 * * * *"  # Default: every hour
    wake_message: str = "Scheduled wake-up"
    timezone: str = "UTC"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **super().to_dict(),
            "type": "cron",
            "cron_expr": self.cron_expr,
            "wake_message": self.wake_message,
            "timezone": self.timezone,
        }


class CronTrigger(BaseTrigger):
    """
    Cron-based wake trigger.
    
    Uses cron expressions to schedule agent wake-ups.
    Supports standard cron syntax:
    - minute (0-59)
    - hour (0-23)
    - day of month (1-31)
    - month (1-12)
    - day of week (0-6, 0=Sunday)
    
    Examples:
    - "0 9 * * *" - Every day at 9 AM
    - "*/30 * * * *" - Every 30 minutes
    - "0 0 * * 1" - Every Monday at midnight
    """
    
    def __init__(self, config: CronTriggerConfig):
        """
        Initialize the cron trigger.
        
        Args:
            config: Cron trigger configuration
        """
        super().__init__(config)
        self.cron_config = config
        self._scheduler = None
        self._simple_task: Optional[asyncio.Task] = None
        self._last_fire: Optional[datetime] = None
        self._fire_count = 0
    
    async def start(self) -> None:
        """Start the cron trigger."""
        if self._running:
            return
        
        self._running = True
        
        if HAS_APSCHEDULER:
            await self._start_apscheduler()
        else:
            await self._start_simple()
        
        logger.info(f"[CronTrigger] Started: {self.name} ({self.cron_config.cron_expr})")
    
    async def _start_apscheduler(self) -> None:
        """Start using APScheduler."""
        self._scheduler = AsyncIOScheduler(timezone=self.cron_config.timezone)
        
        # Parse cron expression
        parts = self.cron_config.cron_expr.split()
        if len(parts) == 5:
            minute, hour, day, month, day_of_week = parts
            trigger = APSCronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
            )
        else:
            # Extended format with seconds
            trigger = APSCronTrigger.from_crontab(self.cron_config.cron_expr)
        
        self._scheduler.add_job(
            self._on_cron_fire,
            trigger=trigger,
            id=self.id,
            name=self.name,
        )
        
        self._scheduler.start()
    
    async def _start_simple(self) -> None:
        """Start using simple interval checking."""
        self._simple_task = asyncio.create_task(self._simple_cron_loop())
    
    async def _simple_cron_loop(self) -> None:
        """Simple cron implementation using interval checking."""
        # Parse cron expression for simple matching
        parts = self.cron_config.cron_expr.split()
        if len(parts) != 5:
            logger.error(f"[CronTrigger] Invalid cron expression: {self.cron_config.cron_expr}")
            return
        
        minute, hour, day, month, day_of_week = parts
        
        while self._running:
            try:
                now = datetime.now()
                
                # Simple matching (supports * and specific values)
                if self._matches_cron(now, minute, hour, day, month, day_of_week):
                    # Check if we already fired this minute
                    if self._last_fire is None or (
                        now.minute != self._last_fire.minute or
                        now.hour != self._last_fire.hour
                    ):
                        await self._on_cron_fire()
                        self._last_fire = now
                
                # Wait until next minute
                await asyncio.sleep(60 - now.second)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[CronTrigger] Error in cron loop: {e}")
                await asyncio.sleep(60)
    
    def _matches_cron(
        self,
        dt: datetime,
        minute: str,
        hour: str,
        day: str,
        month: str,
        day_of_week: str,
    ) -> bool:
        """Check if datetime matches cron expression."""
        return (
            self._matches_field(dt.minute, minute, 0, 59) and
            self._matches_field(dt.hour, hour, 0, 23) and
            self._matches_field(dt.day, day, 1, 31) and
            self._matches_field(dt.month, month, 1, 12) and
            self._matches_field(dt.weekday(), day_of_week, 0, 6)  # Monday=0
        )
    
    def _matches_field(self, value: int, pattern: str, min_val: int, max_val: int) -> bool:
        """Check if value matches cron field pattern."""
        if pattern == "*":
            return True
        
        # Handle step values (*/n)
        if pattern.startswith("*/"):
            step = int(pattern[2:])
            return value % step == 0
        
        # Handle comma-separated values
        if "," in pattern:
            values = [int(v) for v in pattern.split(",")]
            return value in values
        
        # Handle range (n-m)
        if "-" in pattern:
            start, end = map(int, pattern.split("-"))
            return start <= value <= end
        
        # Specific value
        try:
            return value == int(pattern)
        except ValueError:
            return False
    
    async def _on_cron_fire(self) -> None:
        """Handle cron trigger fire."""
        if not self.enabled:
            return
        
        self._fire_count += 1
        self._last_fire = datetime.now()
        
        logger.info(f"[CronTrigger] Fired: {self.name}")
        
        await self._fire(
            message=self.cron_config.wake_message,
            data={
                "fire_time": self._last_fire.isoformat(),
                "fire_count": self._fire_count,
            }
        )
    
    async def stop(self) -> None:
        """Stop the cron trigger."""
        if not self._running:
            return
        
        self._running = False
        
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
        
        if self._simple_task:
            self._simple_task.cancel()
            try:
                await self._simple_task
            except asyncio.CancelledError:
                pass
            self._simple_task = None
        
        logger.info(f"[CronTrigger] Stopped: {self.name}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get trigger information."""
        info = self.cron_config.to_dict()
        info.update({
            "is_running": self._running,
            "last_fire": self._last_fire.isoformat() if self._last_fire else None,
            "fire_count": self._fire_count,
            "using_apscheduler": HAS_APSCHEDULER,
        })
        
        # Get next run time if using APScheduler
        if self._scheduler and HAS_APSCHEDULER:
            job = self._scheduler.get_job(self.id)
            if job and job.next_run_time:
                info["next_run"] = job.next_run_time.isoformat()
        
        return info
