"""
NovAIC Gateway - Configuration Module

Supports both file-based (legacy) and database-backed configuration.
"""

# Legacy file-based manager (for backward compatibility during migration)
from .manager import ConfigManager, AppConfig, ApiKeyEntry, AvailableModel, ProviderType, get_config_manager

# New database-backed manager
from .manager_db import (
    ConfigManagerDB,
    get_config_manager_db,
)

__all__ = [
    # Legacy (sync)
    'ConfigManager',
    'AppConfig', 
    'ApiKeyEntry',
    'AvailableModel',
    'ProviderType',
    'get_config_manager',
    # New (async, database-backed)
    'ConfigManagerDB',
    'get_config_manager_db',
]
