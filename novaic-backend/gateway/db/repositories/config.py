"""
Configuration Repository

Handles all config-related database operations including
API keys, models, and general settings.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..database import Database


class ConfigRepository:
    """Repository for configuration data."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== General Config ====================
    
    def get(self, key: str) -> Optional[Any]:
        """Get a config value (JSON-decoded)."""
        value = self.db.get_config(key)
        if value is not None:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    def set(self, key: str, value: Any):
        """Set a config value (JSON-encoded)."""
        self.db.set_config(key, json.dumps(value))
    
    def get_all(self) -> Dict[str, Any]:
        """Get all config values as dict."""
        rows = self.db.fetchall("SELECT key, value FROM config")
        result = {}
        for row in rows:
            try:
                result[row["key"]] = json.loads(row["value"])
            except json.JSONDecodeError:
                result[row["key"]] = row["value"]
        return result
    
    # ==================== API Keys ====================
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all API keys."""
        return self.db.fetchall(
            "SELECT * FROM api_keys ORDER BY created_at"
        )
    
    def get_api_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get an API key by ID."""
        return self.db.fetchone(
            "SELECT * FROM api_keys WHERE id = ?",
            (key_id,)
        )
    
    def create_api_key(
        self,
        id: str,
        name: str,
        provider: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new API key."""
        created_at = datetime.utcnow().isoformat()
        
        self.db.execute(
            """INSERT INTO api_keys 
               (id, name, provider, api_key, api_base, deployment_name, api_version, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, name, provider, api_key, api_base, deployment_name, api_version, created_at)
        )
        self.db.commit()
        
        return self.get_api_key(id)
    
    def update_api_key(
        self,
        key_id: str,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an API key."""
        # Build update query dynamically
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if api_key is not None:
            updates.append("api_key = ?")
            params.append(api_key)
        if api_base is not None:
            updates.append("api_base = ?")
            params.append(api_base)
        if deployment_name is not None:
            updates.append("deployment_name = ?")
            params.append(deployment_name)
        if api_version is not None:
            updates.append("api_version = ?")
            params.append(api_version)
        
        if not updates:
            return self.get_api_key(key_id)
        
        params.append(key_id)
        self.db.execute(
            f"UPDATE api_keys SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        self.db.commit()
        
        return self.get_api_key(key_id)
    
    def delete_api_key(self, key_id: str) -> bool:
        """Delete an API key (cascades to models)."""
        cursor = self.db.execute(
            "DELETE FROM api_keys WHERE id = ?",
            (key_id,)
        )
        self.db.commit()
        return cursor.rowcount > 0
    
    # ==================== Models ====================
    
    def list_models(
        self,
        api_key_id: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """List candidate models."""
        query = "SELECT * FROM candidate_models WHERE 1=1"
        params = []
        
        if api_key_id:
            query += " AND api_key_id = ?"
            params.append(api_key_id)
        
        if enabled_only:
            query += " AND available = 1"
        
        query += " ORDER BY id"
        return self.db.fetchall(query, tuple(params))
    
    def get_model(
        self,
        model_id: str,
        api_key_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a model by ID and API key ID."""
        return self.db.fetchone(
            "SELECT * FROM candidate_models WHERE id = ? AND api_key_id = ?",
            (model_id, api_key_id)
        )
    
    def create_model(
        self,
        id: str,
        name: str,
        provider: str,
        api_key_id: str,
        enabled: bool = True,
        is_custom: bool = False,
    ) -> Dict[str, Any]:
        """Create or update a model."""
        self.db.execute(
            """INSERT INTO candidate_models 
               (id, name, provider, api_key_id, available, is_custom)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id, api_key_id) DO UPDATE SET
                   name = excluded.name,
                   provider = excluded.provider,
                   available = excluded.available,
                   is_custom = excluded.is_custom""",
            (id, name, provider, api_key_id, 1 if enabled else 0, 1 if is_custom else 0)
        )
        self.db.commit()
        
        return self.get_model(id, api_key_id)
    
    def toggle_model(
        self,
        model_id: str,
        api_key_id: str,
        enabled: bool
    ) -> bool:
        """Enable or disable a model."""
        cursor = self.db.execute(
            "UPDATE candidate_models SET available = ? WHERE id = ? AND api_key_id = ?",
            (1 if enabled else 0, model_id, api_key_id)
        )
        self.db.commit()
        return cursor.rowcount > 0
    
    def delete_model(
        self,
        model_id: str,
        api_key_id: str
    ) -> bool:
        """Delete a model."""
        cursor = self.db.execute(
            "DELETE FROM candidate_models WHERE id = ? AND api_key_id = ?",
            (model_id, api_key_id)
        )
        self.db.commit()
        return cursor.rowcount > 0
    
    def save_models_for_key(
        self,
        api_key_id: str,
        models: List[Dict[str, Any]],
        provider: str
    ):
        """
        Save/merge models for an API key.
        Keeps existing custom models.
        """
        with self.db.transaction():
            # Get existing custom models
            existing_custom = self.db.fetchall(
                "SELECT * FROM candidate_models WHERE api_key_id = ? AND is_custom = 1",
                (api_key_id,)
            )
            custom_ids = {m["id"] for m in existing_custom}
            
            # Delete non-custom models for this key
            self.db.execute(
                "DELETE FROM candidate_models WHERE api_key_id = ? AND is_custom = 0",
                (api_key_id,)
            )
            
            # Insert new models
            new_ids = set()
            for model_data in models:
                model_id = model_data.get("id", "")
                if model_id in custom_ids:
                    continue  # Skip, already exists as custom
                
                new_ids.add(model_id)
                self.db.execute(
                    """INSERT INTO candidate_models 
                       (id, name, provider, api_key_id, available, is_custom)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        model_id,
                        model_data.get("name", model_id),
                        provider,
                        api_key_id,
                        1 if model_data.get("available", model_data.get("enabled", True)) else 0,
                        1 if model_data.get("is_custom", False) else 0,
                    )
                )
