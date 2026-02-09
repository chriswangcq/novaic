"""
Drive Repository

Data access layer for agent_drive table.
Handles agent personality, user profiling, and autonomous behavior configuration.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo

from common.utils.time import utc_now_iso

logger = logging.getLogger(__name__)


class DriveRepository:
    """Repository for agent_drive table."""
    
    def __init__(self, db):
        self.db = db
    
    def _agent_exists(self, agent_id: str) -> bool:
        """Check whether agent_id exists in the agents table."""
        row = self.db.fetchone(
            "SELECT 1 FROM agents WHERE id = ?", (agent_id,)
        )
        return row is not None
    
    def get_or_create(self, agent_id: str) -> Dict[str, Any]:
        """Get drive record, creating default if missing.
        
        If the agent doesn't exist in the agents table the INSERT will fail
        due to FK constraint.  In that case we return sensible defaults so
        that callers (and HTTP endpoints) never crash with a 500.
        """
        # Try insert default first (idempotent)
        try:
            with self.db.transaction(lock_type="agent", resource_id=agent_id):
                self.db.execute(
                    """INSERT OR IGNORE INTO agent_drive (agent_id) VALUES (?)""",
                    (agent_id,)
                )
        except Exception as e:
            # FK constraint violation or other DB error — log and continue
            logger.debug("drive get_or_create INSERT skipped for %s: %s", agent_id, e)
        
        row = self.db.fetchone(
            "SELECT * FROM agent_drive WHERE agent_id = ?",
            (agent_id,)
        )
        
        if not row:
            return self._default_drive(agent_id)
        
        return {
            "agent_id": row["agent_id"],
            "personality": json.loads(row["personality"] or "{}"),
            "communication_style": row["communication_style"] or "friendly",
            "user_profile": json.loads(row["user_profile"] or "{}"),
            "user_active_hours": row["user_active_hours"],
            "proactiveness": row["proactiveness"] or 0.5,
            "min_rest_minutes": row["min_rest_minutes"] or 15,
            "max_rest_minutes": row["max_rest_minutes"] or 120,
            "relationship_level": row["relationship_level"] or 0,
            "interaction_count": row["interaction_count"] or 0,
            "no_response_streak": row["no_response_streak"] or 0,
            "last_proactive_at": row["last_proactive_at"],
            "disabled_tools": json.loads(row["disabled_tools"] or "[]"),
            "custom_instructions": row["custom_instructions"] or "",
            "soul_md": row["soul_md"] or "",
            "heartbeat_md": row["heartbeat_md"] or "",
            "memory_md": row["memory_md"] or "",
            "user_md": row["user_md"] or "",
            "active_hours_start": row["active_hours_start"] or "09:00",
            "active_hours_end": row["active_hours_end"] or "22:00",
            "active_hours_timezone": row["active_hours_timezone"] or "Asia/Shanghai",
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    
    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get drive record without creating (pure read, no lock).
        
        Returns None if not found. Use this for read-only queries.
        """
        row = self.db.fetchone(
            "SELECT * FROM agent_drive WHERE agent_id = ?",
            (agent_id,)
        )
        
        if not row:
            return None
        
        return {
            "agent_id": row["agent_id"],
            "personality": json.loads(row["personality"] or "{}"),
            "communication_style": row["communication_style"] or "friendly",
            "user_profile": json.loads(row["user_profile"] or "{}"),
            "user_active_hours": row["user_active_hours"],
            "proactiveness": row["proactiveness"] or 0.5,
            "min_rest_minutes": row["min_rest_minutes"] or 15,
            "max_rest_minutes": row["max_rest_minutes"] or 120,
            "relationship_level": row["relationship_level"] or 0,
            "interaction_count": row["interaction_count"] or 0,
            "no_response_streak": row["no_response_streak"] or 0,
            "last_proactive_at": row["last_proactive_at"],
            "disabled_tools": json.loads(row["disabled_tools"] or "[]"),
            "custom_instructions": row["custom_instructions"] or "",
            "soul_md": row["soul_md"] or "",
            "heartbeat_md": row["heartbeat_md"] or "",
            "memory_md": row["memory_md"] or "",
            "user_md": row["user_md"] or "",
            "active_hours_start": row["active_hours_start"] or "09:00",
            "active_hours_end": row["active_hours_end"] or "22:00",
            "active_hours_timezone": row["active_hours_timezone"] or "Asia/Shanghai",
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    
    def update_profile(
        self,
        agent_id: str,
        key: str,
        value: Any,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a key in user_profile JSON."""
        now = utc_now_iso()
        
        # Ensure record exists — if the agent is missing we return early
        current = self.get_or_create(agent_id)
        if not self._agent_exists(agent_id):
            logger.debug("update_profile: agent %s not in agents table, skipping", agent_id)
            return {
                "success": True,
                "key": key,
                "profile_keys": list(current["user_profile"].keys()),
                "skipped": True,
            }
        
        # Read current profile
        row = self.db.fetchone(
            "SELECT user_profile FROM agent_drive WHERE agent_id = ?",
            (agent_id,)
        )
        profile = json.loads(row["user_profile"] or "{}") if row else {}
        
        # Update key
        profile[key] = value
        
        try:
            with self.db.transaction(lock_type="agent", resource_id=agent_id):
                self.db.execute(
                    """UPDATE agent_drive 
                       SET user_profile = ?, updated_at = ?
                       WHERE agent_id = ?""",
                    (json.dumps(profile, ensure_ascii=False), now, agent_id)
                )
        except Exception as e:
            logger.warning("update_profile failed for %s: %s", agent_id, e)
            return {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "key": key,
            "profile_keys": list(profile.keys()),
        }
    
    def update_drive(
        self,
        agent_id: str,
        relationship_delta: Optional[int] = None,
        proactiveness_delta: Optional[float] = None,
        reason: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Update drive fields with deltas for relationship and proactiveness."""
        now = utc_now_iso()
        
        # Ensure record exists
        current = self.get_or_create(agent_id)
        if not self._agent_exists(agent_id):
            logger.debug("update_drive: agent %s not in agents table, skipping", agent_id)
            return {"success": True, "agent_id": agent_id, "skipped": True}
        
        updates = ["updated_at = ?"]
        params = [now]
        
        if relationship_delta is not None:
            new_level = max(0, min(100, current["relationship_level"] + relationship_delta))
            updates.append("relationship_level = ?")
            params.append(new_level)
        
        if proactiveness_delta is not None:
            new_proactive = max(0.0, min(1.0, current["proactiveness"] + proactiveness_delta))
            updates.append("proactiveness = ?")
            params.append(new_proactive)
        
        # Direct field updates
        for field in ("communication_style", "user_active_hours", "min_rest_minutes", "max_rest_minutes"):
            if field in kwargs and kwargs[field] is not None:
                updates.append(f"{field} = ?")
                params.append(kwargs[field])
        
        set_clause = ", ".join(updates)
        params.append(agent_id)
        
        try:
            with self.db.transaction(lock_type="agent", resource_id=agent_id):
                self.db.execute(
                    f"UPDATE agent_drive SET {set_clause} WHERE agent_id = ?",
                    tuple(params)
                )
        except Exception as e:
            logger.warning("update_drive failed for %s: %s", agent_id, e)
            return {"success": False, "agent_id": agent_id, "error": str(e)}
        
        return {"success": True, "agent_id": agent_id}
    
    def increment_interaction(self, agent_id: str) -> Dict[str, Any]:
        """Atomically increment interaction_count."""
        now = utc_now_iso()
        self.get_or_create(agent_id)
        
        if not self._agent_exists(agent_id):
            logger.debug("increment_interaction: agent %s not in agents table, skipping", agent_id)
            return {"success": True, "skipped": True}
        
        try:
            with self.db.transaction(lock_type="agent", resource_id=agent_id):
                self.db.execute(
                    """UPDATE agent_drive 
                       SET interaction_count = interaction_count + 1, 
                           no_response_streak = 0,
                           updated_at = ?
                       WHERE agent_id = ?""",
                    (now, agent_id)
                )
        except Exception as e:
            logger.warning("increment_interaction failed for %s: %s", agent_id, e)
            return {"success": False, "error": str(e)}
        
        return {"success": True}
    
    def set_last_proactive(self, agent_id: str) -> Dict[str, Any]:
        """Set last_proactive_at to now."""
        now = utc_now_iso()
        self.get_or_create(agent_id)
        
        if not self._agent_exists(agent_id):
            logger.debug("set_last_proactive: agent %s not in agents table, skipping", agent_id)
            return {"success": True, "last_proactive_at": None, "skipped": True}
        
        try:
            with self.db.transaction(lock_type="agent", resource_id=agent_id):
                self.db.execute(
                    """UPDATE agent_drive 
                       SET last_proactive_at = ?, no_response_streak = no_response_streak + 1, updated_at = ?
                       WHERE agent_id = ?""",
                    (now, now, agent_id)
                )
        except Exception as e:
            logger.warning("set_last_proactive failed for %s: %s", agent_id, e)
            return {"success": False, "error": str(e)}
        
        return {"success": True, "last_proactive_at": now}
    
    def _default_drive(self, agent_id: str) -> Dict[str, Any]:
        """Return default drive values."""
        return {
            "agent_id": agent_id,
            "personality": {},
            "communication_style": "friendly",
            "user_profile": {},
            "user_active_hours": None,
            "proactiveness": 0.5,
            "min_rest_minutes": 15,
            "max_rest_minutes": 120,
            "relationship_level": 0,
            "interaction_count": 0,
            "no_response_streak": 0,
            "last_proactive_at": None,
            "disabled_tools": [],
            "custom_instructions": "",
            "soul_md": "",
            "heartbeat_md": "",
            "memory_md": "",
            "user_md": "",
            "active_hours_start": "09:00",
            "active_hours_end": "22:00",
            "active_hours_timezone": "Asia/Shanghai",
            "created_at": None,
            "updated_at": None,
        }
    
    def update_bootstrap_files(
        self,
        agent_id: str,
        soul_md: Optional[str] = None,
        heartbeat_md: Optional[str] = None,
        memory_md: Optional[str] = None,
        user_md: Optional[str] = None,
        active_hours_start: Optional[str] = None,
        active_hours_end: Optional[str] = None,
        active_hours_timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update bootstrap markdown files and active hours config."""
        now = utc_now_iso()
        
        # Ensure record exists
        self.get_or_create(agent_id)
        if not self._agent_exists(agent_id):
            logger.debug("update_bootstrap_files: agent %s not in agents table, skipping", agent_id)
            return {"success": True, "agent_id": agent_id, "skipped": True}
        
        updates = ["updated_at = ?"]
        params = [now]
        
        # Only update non-None fields
        field_mapping = {
            "soul_md": soul_md,
            "heartbeat_md": heartbeat_md,
            "memory_md": memory_md,
            "user_md": user_md,
            "active_hours_start": active_hours_start,
            "active_hours_end": active_hours_end,
            "active_hours_timezone": active_hours_timezone,
        }
        
        for field, value in field_mapping.items():
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value)
        
        # If no fields to update, return early
        if len(updates) == 1:
            return {"success": True, "agent_id": agent_id, "no_changes": True}
        
        set_clause = ", ".join(updates)
        params.append(agent_id)
        
        try:
            with self.db.transaction(lock_type="agent", resource_id=agent_id):
                self.db.execute(
                    f"UPDATE agent_drive SET {set_clause} WHERE agent_id = ?",
                    tuple(params)
                )
        except Exception as e:
            logger.warning("update_bootstrap_files failed for %s: %s", agent_id, e)
            return {"success": False, "agent_id": agent_id, "error": str(e)}
        
        return {"success": True, "agent_id": agent_id}
    
    def is_active_hours(self, agent_id: str) -> bool:
        """Check if current time is within user's active hours."""
        drive = self.get_or_create(agent_id)
        
        active_hours_start = drive.get("active_hours_start", "09:00")
        active_hours_end = drive.get("active_hours_end", "22:00")
        active_hours_timezone = drive.get("active_hours_timezone", "Asia/Shanghai")
        
        try:
            tz = ZoneInfo(active_hours_timezone)
        except Exception:
            # Fallback to Asia/Shanghai if timezone is invalid
            logger.warning("Invalid timezone %s for agent %s, using Asia/Shanghai", active_hours_timezone, agent_id)
            tz = ZoneInfo("Asia/Shanghai")
        
        # Get current time in the user's timezone
        now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
        now_local = now_utc.astimezone(tz)
        current_time = now_local.strftime("%H:%M")
        
        # Parse start and end times
        start_time = active_hours_start
        end_time = active_hours_end
        
        # Handle overnight ranges (e.g., 22:00 - 06:00)
        if start_time <= end_time:
            # Normal range (e.g., 09:00 - 22:00)
            return start_time <= current_time <= end_time
        else:
            # Overnight range (e.g., 22:00 - 06:00)
            return current_time >= start_time or current_time <= end_time
