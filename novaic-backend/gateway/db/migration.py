"""
Data Migration Script

Migrates existing file-based data to SQLite database.
Also includes schema migrations for foreign key constraints.
"""

import os
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from common.db import Database
from common.utils.time import utc_now_iso
from .access import get_db

logger = logging.getLogger(__name__)


def migrate_config(db: Database, data_dir: Path) -> bool:
    """Migrate config.json to database."""
    config_file = data_dir / "config.json"
    
    if not config_file.exists():
        logger.info("[Migration] No config.json found, skipping")
        return False
    
    logger.info(f"[Migration] Migrating config from {config_file}")
    
    try:
        with open(config_file, "r") as f:
            data = json.load(f)
        
        with db.transaction("global"):
            # Migrate general settings
            if "version" in data:
                db.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    ("version", json.dumps(data["version"]))
                )
            if "default_model" in data:
                db.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    ("default_model", json.dumps(data["default_model"]))
                )
            if "max_tokens" in data:
                db.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    ("max_tokens", json.dumps(data["max_tokens"]))
                )
            if "max_iterations" in data:
                db.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    ("max_iterations", json.dumps(data["max_iterations"]))
                )
            if "visible_shell" in data:
                db.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    ("visible_shell", json.dumps(data["visible_shell"]))
                )
            
            # Migrate API keys
            for key in data.get("api_keys", []):
                db.execute(
                    """INSERT OR REPLACE INTO api_keys 
                       (id, name, provider, api_key, api_base, deployment_name, api_version, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        key["id"],
                        key["name"],
                        key["provider"],
                        key.get("api_key"),
                        key.get("api_base"),
                        key.get("deployment_name"),
                        key.get("api_version"),
                        key.get("created_at", utc_now_iso()),
                    )
                )
            
            # Migrate models (candidate_models preferred, fallback to available_models)
            models = data.get("candidate_models", data.get("available_models", []))
            for model in models:
                db.execute(
                    """INSERT OR REPLACE INTO candidate_models 
                       (id, name, provider, api_key_id, available, is_custom)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        model["id"],
                        model["name"],
                        model["provider"],
                        model["api_key_id"],
                        1 if model.get("available", model.get("enabled", True)) else 0,
                        1 if model.get("is_custom", False) else 0,
                    )
                )
        
        logger.info(f"[Migration] Migrated config: {len(data.get('api_keys', []))} API keys, {len(models)} models")
        
        # Backup old file
        backup_file = config_file.with_suffix(".json.bak")
        config_file.rename(backup_file)
        logger.info(f"[Migration] Backed up config.json to {backup_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"[Migration] Failed to migrate config: {e}")
        return False


def migrate_agents(db: Database, data_dir: Path) -> bool:
    """Migrate agents.json to database."""
    agents_file = data_dir / "agents.json"
    
    if not agents_file.exists():
        logger.info("[Migration] No agents.json found, skipping")
        return False
    
    logger.info(f"[Migration] Migrating agents from {agents_file}")
    
    try:
        with open(agents_file, "r") as f:
            data = json.load(f)
        
        with db.transaction("global"):
            # Migrate agents
            for agent in data.get("agents", []):
                # Extract VM config and ports
                vm_config = agent.get("vm", {})
                ports = vm_config.pop("ports", {})
                
                db.execute(
                    """INSERT OR REPLACE INTO agents 
                       (id, name, created_at, vm_config, ports, status)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        agent["id"],
                        agent["name"],
                        agent.get("created_at", utc_now_iso()),
                        json.dumps(vm_config),
                        json.dumps(ports),
                        agent.get("status", "stopped"),
                    )
                )
        
        logger.info(f"[Migration] Migrated {len(data.get('agents', []))} agents")
        
        # Backup old file
        backup_file = agents_file.with_suffix(".json.bak")
        agents_file.rename(backup_file)
        logger.info(f"[Migration] Backed up agents.json to {backup_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"[Migration] Failed to migrate agents: {e}")
        return False


def migrate_sessions(db: Database, data_dir: Path) -> bool:
    """Migrate session JSONL files to database."""
    sessions_dir = data_dir / "sessions"
    
    if not sessions_dir.exists():
        logger.info("[Migration] No sessions directory found, skipping")
        return False
    
    session_files = list(sessions_dir.glob("*.jsonl"))
    if not session_files:
        logger.info("[Migration] No session files found, skipping")
        return False
    
    logger.info(f"[Migration] Migrating {len(session_files)} session files")
    
    migrated = 0
    for session_file in session_files:
        try:
            # Extract session ID from filename
            session_id = session_file.stem.replace("_", ":")
            
            # Create session
            db.execute(
                """INSERT OR IGNORE INTO sessions (id, created_at, updated_at)
                   VALUES (?, ?, ?)""",
                (session_id, utc_now_iso(), utc_now_iso())
            )
            
            # Read and migrate entries
            with open(session_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        entry_type = entry.get("type", "message")
                        
                        if entry_type == "message":
                            db.execute(
                                """INSERT INTO session_messages 
                                   (session_id, type, role, content, timestamp, metadata)
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                (
                                    session_id,
                                    "message",
                                    entry.get("role"),
                                    json.dumps(entry.get("content")) if not isinstance(entry.get("content"), str) else entry.get("content"),
                                    entry.get("timestamp", utc_now_iso()),
                                    json.dumps(entry.get("metadata", {})),
                                )
                            )
                        elif entry_type == "compaction_summary":
                            db.execute(
                                """INSERT INTO session_messages 
                                   (session_id, type, content, timestamp, compacted_count, original_tokens, summary_tokens)
                                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (
                                    session_id,
                                    "compaction_summary",
                                    entry.get("summary"),
                                    entry.get("timestamp", utc_now_iso()),
                                    entry.get("compacted_count"),
                                    entry.get("original_tokens"),
                                    entry.get("summary_tokens"),
                                )
                            )
                    except json.JSONDecodeError:
                        continue
            
            db.commit()
            migrated += 1
            
            # Backup old file
            backup_file = session_file.with_suffix(".jsonl.bak")
            session_file.rename(backup_file)
            
        except Exception as e:
            logger.error(f"[Migration] Failed to migrate session {session_file}: {e}")
    
    logger.info(f"[Migration] Migrated {migrated} sessions")
    
    # Also migrate metadata files
    for meta_file in sessions_dir.glob("*.meta.json"):
        try:
            backup_file = meta_file.with_suffix(".json.bak")
            meta_file.rename(backup_file)
        except Exception:
            pass
    
    return migrated > 0


def migrate_add_foreign_keys(db: Database) -> bool:
    """Add foreign key constraints to existing tables.
    
    Note: SQLite doesn't support ADD CONSTRAINT directly,
    so we document the new schema and apply on fresh installs.
    For existing databases, foreign keys will be enforced by application logic.
    """
    try:
        # Check if migration is already applied by examining table schema
        cursor = db.conn.execute("PRAGMA foreign_key_list(chat_messages)")
        existing_fks = cursor.fetchall()
        
        if existing_fks:
            logger.info("[Migration] Foreign key constraints already exist, skipping")
            return True
        
        logger.warning("[Migration] Foreign key migration requires manual intervention")
        logger.warning("[Migration] New installs will use schema.py with foreign keys")
        logger.warning("[Migration] Existing databases: foreign keys will be enforced by application logic")
        
        # For existing databases, we can't easily add foreign keys without recreating tables
        # The safest approach is:
        # 1. New installs get foreign keys from schema.py
        # 2. Existing installs rely on application logic in delete_agent()
        
        return True
        
    except Exception as e:
        logger.error(f"[Migration] Foreign key migration check failed: {e}")
        return False


def run_migration(db: Optional[Database] = None) -> Dict[str, bool]:
    """Run all migrations."""
    if db is None:
        db = get_db()
        db.connect()
    
    data_dir = Path(os.environ.get("NOVAIC_DATA_DIR", "."))
    
    logger.info(f"[Migration] Starting migration from {data_dir}")
    
    results = {
        "config": migrate_config(db, data_dir),
        "agents": migrate_agents(db, data_dir),
        "sessions": migrate_sessions(db, data_dir),
        "foreign_keys": migrate_add_foreign_keys(db),
    }
    
    logger.info(f"[Migration] Migration complete: {results}")
    
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
