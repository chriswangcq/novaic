"""
NovAIC Gateway - Database-backed Configuration Manager

Manages API keys, models, and settings using SQLite.
This replaces the file-based ConfigManager.
"""

import json
import uuid
import asyncio
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from db.database import get_database, Database
from db.repositories.config import ConfigRepository


class ProviderType(str, Enum):
    """LLM Provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    OPENAI_COMPATIBLE = "openai_compatible"
    
    @property
    def display_name(self) -> str:
        names = {
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "google": "Google AI",
            "azure": "Azure OpenAI",
            "openai_compatible": "OpenAI Compatible",
        }
        return names.get(self.value, self.value)
    
    @property
    def default_base_url(self) -> Optional[str]:
        urls = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com",
            "google": "https://generativelanguage.googleapis.com/v1beta",
        }
        return urls.get(self.value)


class ApiKeyEntry(BaseModel):
    """API Key configuration entry"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    provider: ProviderType
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_public(self) -> dict:
        """Return public version (hides sensitive data)"""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider.value,
            "has_api_key": bool(self.api_key and self.api_key.strip()),
            "api_base": self.api_base,
            "deployment_name": self.deployment_name,
            "api_version": self.api_version,
            "created_at": self.created_at,
        }
    
    def get_effective_base_url(self) -> str:
        """Get the effective API base URL"""
        return self.api_base or self.provider.default_base_url or ""


class AvailableModel(BaseModel):
    """Available model configuration"""
    id: str
    name: str
    provider: ProviderType
    api_key_id: str
    enabled: bool = True
    is_custom: bool = False


class AppConfig(BaseModel):
    """Main application configuration (for compatibility)"""
    version: int = 2
    api_keys: List[ApiKeyEntry] = []
    available_models: List[AvailableModel] = []
    default_model: str = "gpt-4o"
    max_tokens: int = 4096
    max_iterations: int = 20
    visible_shell: bool = False
    
    def to_public(self) -> dict:
        """Return public version (hides API keys)"""
        return {
            "version": self.version,
            "api_keys": [k.to_public() for k in self.api_keys],
            "available_models": [m.model_dump() for m in self.available_models],
            "default_model": self.default_model,
            "max_tokens": self.max_tokens,
            "max_iterations": self.max_iterations,
            "visible_shell": self.visible_shell,
        }
    
    def get_api_key_by_id(self, key_id: str) -> Optional[ApiKeyEntry]:
        """Get API key entry by ID"""
        for key in self.api_keys:
            if key.id == key_id:
                return key
        return None
    
    def get_enabled_models(self) -> List[AvailableModel]:
        """Get only enabled models"""
        return [m for m in self.available_models if m.enabled]


class ConfigManagerDB:
    """
    Database-backed Configuration Manager.
    
    All operations go directly to SQLite database.
    No in-memory caching - every read fetches from DB.
    """
    
    def __init__(self, db: Optional[Database] = None):
        self._db = db
        self._repo: Optional[ConfigRepository] = None
    
    @property
    def db(self) -> Database:
        if self._db is None:
            self._db = get_database()
        return self._db
    
    @property
    def repo(self) -> ConfigRepository:
        if self._repo is None:
            self._repo = ConfigRepository(self.db)
        return self._repo
    
    async def load(self) -> AppConfig:
        """Load full configuration from database."""
        # Get general config
        config_data = await self.repo.get_all()
        
        # Get API keys
        api_keys_data = await self.repo.list_api_keys()
        api_keys = []
        for k in api_keys_data:
            api_keys.append(ApiKeyEntry(
                id=k["id"],
                name=k["name"],
                provider=ProviderType(k["provider"]),
                api_key=k.get("api_key"),
                api_base=k.get("api_base"),
                deployment_name=k.get("deployment_name"),
                api_version=k.get("api_version"),
                created_at=k.get("created_at", ""),
            ))
        
        # Get models
        models_data = await self.repo.list_models()
        models = []
        for m in models_data:
            models.append(AvailableModel(
                id=m["id"],
                name=m["name"],
                provider=ProviderType(m["provider"]),
                api_key_id=m["api_key_id"],
                enabled=bool(m.get("enabled", 1)),
                is_custom=bool(m.get("is_custom", 0)),
            ))
        
        return AppConfig(
            version=config_data.get("version", 2),
            api_keys=api_keys,
            available_models=models,
            default_model=config_data.get("default_model", "gpt-4o"),
            max_tokens=config_data.get("max_tokens", 4096),
            max_iterations=config_data.get("max_iterations", 20),
            visible_shell=config_data.get("visible_shell", False),
        )
    
    # ==================== API Key Management ====================
    
    async def add_api_key(
        self,
        provider: ProviderType,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> ApiKeyEntry:
        """Add a new API key entry."""
        # Generate name if not provided
        if not name:
            existing = await self.repo.list_api_keys()
            count = sum(1 for k in existing if k["provider"] == provider.value)
            name = f"{provider.display_name} #{count + 1}"
        
        key_id = str(uuid.uuid4())
        
        await self.repo.create_api_key(
            id=key_id,
            name=name,
            provider=provider.value,
            api_key=api_key,
            api_base=api_base,
            deployment_name=deployment_name,
            api_version=api_version,
        )
        
        return ApiKeyEntry(
            id=key_id,
            name=name,
            provider=provider,
            api_key=api_key,
            api_base=api_base,
            deployment_name=deployment_name,
            api_version=api_version,
        )
    
    async def update_api_key(
        self,
        key_id: str,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> Optional[ApiKeyEntry]:
        """Update an existing API key entry."""
        result = await self.repo.update_api_key(
            key_id=key_id,
            name=name,
            api_key=api_key,
            api_base=api_base,
            deployment_name=deployment_name,
            api_version=api_version,
        )
        
        if result:
            return ApiKeyEntry(
                id=result["id"],
                name=result["name"],
                provider=ProviderType(result["provider"]),
                api_key=result.get("api_key"),
                api_base=result.get("api_base"),
                deployment_name=result.get("deployment_name"),
                api_version=result.get("api_version"),
                created_at=result.get("created_at", ""),
            )
        return None
    
    async def delete_api_key(self, key_id: str) -> bool:
        """Delete an API key entry (cascades to models)."""
        return await self.repo.delete_api_key(key_id)
    
    # ==================== Model Management ====================
    
    async def add_model(
        self,
        model_id: str,
        name: str,
        provider: ProviderType,
        api_key_id: str,
        enabled: bool = True,
        is_custom: bool = False,
    ) -> AvailableModel:
        """Add a new available model."""
        await self.repo.create_model(
            id=model_id,
            name=name,
            provider=provider.value,
            api_key_id=api_key_id,
            enabled=enabled,
            is_custom=is_custom,
        )
        
        return AvailableModel(
            id=model_id,
            name=name,
            provider=provider,
            api_key_id=api_key_id,
            enabled=enabled,
            is_custom=is_custom,
        )
    
    async def toggle_model(
        self,
        model_id: str,
        api_key_id: str,
        enabled: bool
    ) -> bool:
        """Enable or disable a model."""
        return await self.repo.toggle_model(model_id, api_key_id, enabled)
    
    async def delete_model(self, model_id: str, api_key_id: str) -> bool:
        """Delete a model."""
        return await self.repo.delete_model(model_id, api_key_id)
    
    async def save_models_for_key(
        self,
        api_key_id: str,
        models: List[dict]
    ):
        """Save/merge models for an API key."""
        # Get API key to determine provider
        key_data = await self.repo.get_api_key(api_key_id)
        if not key_data:
            return
        
        await self.repo.save_models_for_key(
            api_key_id=api_key_id,
            models=models,
            provider=key_data["provider"],
        )
    
    # ==================== Settings ====================
    
    async def update_settings(
        self,
        default_model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        max_iterations: Optional[int] = None,
        visible_shell: Optional[bool] = None,
    ):
        """Update common settings."""
        if default_model is not None:
            await self.repo.set("default_model", default_model)
        if max_tokens is not None:
            await self.repo.set("max_tokens", max_tokens)
        if max_iterations is not None:
            await self.repo.set("max_iterations", max_iterations)
        if visible_shell is not None:
            await self.repo.set("visible_shell", visible_shell)
    
    async def set_default_model(self, model_id: str):
        """Set the default model."""
        await self.repo.set("default_model", model_id)
    
    async def get_default_model(self) -> str:
        """Get the default model."""
        return await self.repo.get("default_model") or "gpt-4o"


# ==================== Sync Wrapper for Backward Compatibility ====================

class ConfigManager:
    """
    Synchronous wrapper around ConfigManagerDB for backward compatibility.
    
    Uses asyncio.run() to execute async operations.
    In new code, prefer using ConfigManagerDB directly.
    """
    
    def __init__(self):
        self._async_manager = ConfigManagerDB()
        self._loop = None
    
    def _run_async(self, coro):
        """Run an async coroutine synchronously."""
        try:
            loop = asyncio.get_running_loop()
            # If already in async context, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(coro)
    
    def load(self) -> AppConfig:
        """Load configuration."""
        return self._run_async(self._async_manager.load())
    
    def reload(self) -> AppConfig:
        """Reload configuration (same as load for DB version)."""
        return self.load()
    
    def add_api_key(self, **kwargs) -> ApiKeyEntry:
        """Add API key."""
        if "provider" in kwargs and isinstance(kwargs["provider"], str):
            kwargs["provider"] = ProviderType(kwargs["provider"])
        return self._run_async(self._async_manager.add_api_key(**kwargs))
    
    def update_api_key(self, key_id: str, **kwargs) -> Optional[ApiKeyEntry]:
        """Update API key."""
        return self._run_async(self._async_manager.update_api_key(key_id, **kwargs))
    
    def delete_api_key(self, key_id: str) -> bool:
        """Delete API key."""
        return self._run_async(self._async_manager.delete_api_key(key_id))
    
    def add_model(self, **kwargs) -> AvailableModel:
        """Add model."""
        if "provider" in kwargs and isinstance(kwargs["provider"], str):
            kwargs["provider"] = ProviderType(kwargs["provider"])
        return self._run_async(self._async_manager.add_model(**kwargs))
    
    def toggle_model(self, model_id: str, api_key_id: str, enabled: bool) -> bool:
        """Toggle model."""
        return self._run_async(self._async_manager.toggle_model(model_id, api_key_id, enabled))
    
    def delete_model(self, model_id: str, api_key_id: str) -> bool:
        """Delete model."""
        return self._run_async(self._async_manager.delete_model(model_id, api_key_id))
    
    def save_models_for_key(self, api_key_id: str, models: List[dict]):
        """Save models for key."""
        return self._run_async(self._async_manager.save_models_for_key(api_key_id, models))
    
    def update_settings(self, **kwargs):
        """Update settings."""
        return self._run_async(self._async_manager.update_settings(**kwargs))
    
    def set_default_model(self, model_id: str):
        """Set default model."""
        return self._run_async(self._async_manager.set_default_model(model_id))


# Global instances
_config_manager: Optional[ConfigManager] = None
_config_manager_db: Optional[ConfigManagerDB] = None


def get_config_manager() -> ConfigManager:
    """Get the global sync config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config_manager_db() -> ConfigManagerDB:
    """Get the global async config manager instance."""
    global _config_manager_db
    if _config_manager_db is None:
        _config_manager_db = ConfigManagerDB()
    return _config_manager_db
