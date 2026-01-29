"""
NovAIC Gateway - Configuration Module

Uses SQLite database for persistent configuration storage.
"""

# Database-backed manager (primary)
from .manager_db import (
    ConfigManager,
    ConfigManagerDB,
    AppConfig,
    ApiKeyEntry,
    AvailableModel,
    ProviderType,
    get_config_manager,
    get_config_manager_db,
)

__all__ = [
    # Sync wrapper (backward compatible)
    'ConfigManager',
    'AppConfig', 
    'ApiKeyEntry',
    'AvailableModel',
    'ProviderType',
    'get_config_manager',
    # Async (primary, database-backed)
    'ConfigManagerDB',
    'get_config_manager_db',
]
