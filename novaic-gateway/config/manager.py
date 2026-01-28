"""
NovAIC Gateway - Configuration Manager

Manages API keys, models, and settings.
Migrated from Tauri app_config.rs to Python.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
from enum import Enum
from datetime import datetime
import json
import uuid


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
    
    # Azure specific
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
    id: str                    # Model ID e.g. "gpt-4o"
    name: str                  # Display name e.g. "GPT-4o"
    provider: ProviderType
    api_key_id: str           # Which API key provides this model
    enabled: bool = True      # Whether enabled as candidate
    is_custom: bool = False   # Whether this is a custom model


class AppConfig(BaseModel):
    """Main application configuration"""
    version: int = 2
    
    # API Keys list
    api_keys: List[ApiKeyEntry] = []
    
    # Available models (discovered from API keys)
    available_models: List[AvailableModel] = []
    
    # Default model to use
    default_model: str = "gpt-4o"
    
    # Common LLM settings
    max_tokens: int = 4096
    
    # Agent settings
    max_iterations: int = 20
    
    # Execution display
    visible_shell: bool = False
    
    # MCP Server 配置
    # CID 用于生成 Unix socket 路径: /tmp/novaic-mcp-{cid}.sock
    vsock_cid: int = 3       # VM Context ID (3+)
    
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
            "cid": self.vsock_cid,
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


class ConfigManager:
    """
    Configuration manager that handles reading/writing config files.
    
    Config file location: ~/.novaic/config.json
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".novaic"
        self.config_file = self.config_dir / "config.json"
        self._config: Optional[AppConfig] = None
    
    def _ensure_dir(self):
        """Ensure config directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> AppConfig:
        """Load configuration from file"""
        if self._config is not None:
            return self._config
        
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                # Convert provider strings to enum
                if "api_keys" in data:
                    for key in data["api_keys"]:
                        if isinstance(key.get("provider"), str):
                            key["provider"] = ProviderType(key["provider"])
                if "available_models" in data:
                    for model in data["available_models"]:
                        if isinstance(model.get("provider"), str):
                            model["provider"] = ProviderType(model["provider"])
                self._config = AppConfig(**data)
            except Exception as e:
                print(f"[Config] Failed to load config: {e}, using defaults")
                self._config = AppConfig()
        else:
            self._config = AppConfig()
        
        return self._config
    
    def save(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to file"""
        self._ensure_dir()
        
        if config is not None:
            self._config = config
        
        if self._config is None:
            return
        
        # Serialize with proper enum handling
        data = self._config.model_dump()
        
        # Convert enums to strings
        for key in data.get("api_keys", []):
            if isinstance(key.get("provider"), ProviderType):
                key["provider"] = key["provider"].value
        for model in data.get("available_models", []):
            if isinstance(model.get("provider"), ProviderType):
                model["provider"] = model["provider"].value
        
        self.config_file.write_text(json.dumps(data, indent=2, default=str))
        
        # Set restricted permissions on Unix
        try:
            import os
            os.chmod(self.config_file, 0o600)
        except Exception:
            pass
    
    def reload(self) -> AppConfig:
        """Force reload configuration from file"""
        self._config = None
        return self.load()
    
    # ==================== API Key Management ====================
    
    def add_api_key(
        self,
        provider: ProviderType,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> ApiKeyEntry:
        """Add a new API key entry"""
        config = self.load()
        
        # Generate name if not provided
        if not name:
            count = sum(1 for k in config.api_keys if k.provider == provider)
            name = f"{provider.display_name} #{count + 1}"
        
        entry = ApiKeyEntry(
            name=name,
            provider=provider,
            api_key=api_key,
            api_base=api_base,
            deployment_name=deployment_name,
            api_version=api_version,
        )
        
        config.api_keys.append(entry)
        self.save(config)
        
        return entry
    
    def update_api_key(
        self,
        key_id: str,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> Optional[ApiKeyEntry]:
        """Update an existing API key entry"""
        config = self.load()
        
        for entry in config.api_keys:
            if entry.id == key_id:
                if name is not None:
                    entry.name = name
                if api_key is not None:
                    entry.api_key = api_key
                if api_base is not None:
                    entry.api_base = api_base
                if deployment_name is not None:
                    entry.deployment_name = deployment_name
                if api_version is not None:
                    entry.api_version = api_version
                
                self.save(config)
                return entry
        
        return None
    
    def delete_api_key(self, key_id: str) -> bool:
        """Delete an API key entry"""
        config = self.load()
        
        original_count = len(config.api_keys)
        config.api_keys = [k for k in config.api_keys if k.id != key_id]
        
        # Also remove models associated with this key
        config.available_models = [m for m in config.available_models if m.api_key_id != key_id]
        
        if len(config.api_keys) < original_count:
            self.save(config)
            return True
        
        return False
    
    # ==================== Model Management ====================
    
    def add_model(
        self,
        model_id: str,
        name: str,
        provider: ProviderType,
        api_key_id: str,
        enabled: bool = True,
        is_custom: bool = False,
    ) -> AvailableModel:
        """Add a new available model"""
        config = self.load()
        
        model = AvailableModel(
            id=model_id,
            name=name,
            provider=provider,
            api_key_id=api_key_id,
            enabled=enabled,
            is_custom=is_custom,
        )
        
        config.available_models.append(model)
        self.save(config)
        
        return model
    
    def toggle_model(self, model_id: str, api_key_id: str, enabled: bool) -> bool:
        """Enable or disable a model"""
        config = self.load()
        
        for model in config.available_models:
            if model.id == model_id and model.api_key_id == api_key_id:
                model.enabled = enabled
                self.save(config)
                return True
        
        return False
    
    def delete_model(self, model_id: str, api_key_id: str) -> bool:
        """Delete a model"""
        config = self.load()
        
        original_count = len(config.available_models)
        config.available_models = [
            m for m in config.available_models 
            if not (m.id == model_id and m.api_key_id == api_key_id)
        ]
        
        if len(config.available_models) < original_count:
            self.save(config)
            return True
        
        return False
    
    def save_models_for_key(self, api_key_id: str, models: List[dict]) -> None:
        """Save/replace all models for an API key"""
        config = self.load()
        
        # Get the API key to determine provider
        api_key = config.get_api_key_by_id(api_key_id)
        if not api_key:
            return
        
        # Remove existing models for this key
        config.available_models = [m for m in config.available_models if m.api_key_id != api_key_id]
        
        # Add new models
        for model_data in models:
            model = AvailableModel(
                id=model_data.get("id", ""),
                name=model_data.get("name", model_data.get("id", "")),
                provider=api_key.provider,
                api_key_id=api_key_id,
                enabled=model_data.get("enabled", True),
                is_custom=model_data.get("is_custom", False),
            )
            config.available_models.append(model)
        
        self.save(config)
    
    # ==================== Settings ====================
    
    def update_settings(
        self,
        default_model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        max_iterations: Optional[int] = None,
        visible_shell: Optional[bool] = None,
        cid: Optional[int] = None,
    ) -> None:
        """Update common settings"""
        config = self.load()
        
        if default_model is not None:
            config.default_model = default_model
        if max_tokens is not None:
            config.max_tokens = max_tokens
        if max_iterations is not None:
            config.max_iterations = max_iterations
        if visible_shell is not None:
            config.visible_shell = visible_shell
        if cid is not None:
            config.vsock_cid = cid
        
        self.save(config)
    
    def set_default_model(self, model_id: str) -> None:
        """Set the default model"""
        config = self.load()
        config.default_model = model_id
        self.save(config)


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
