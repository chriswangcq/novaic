"""
NovAIC Gateway - Configuration Module

Uses SQLite database for persistent configuration storage.
v11: Added multi-process settings.
"""

# Database-backed manager (primary)
from .manager_db import (
    ConfigManager,
    ConfigManagerDB,
    AppConfig,
    ApiKeyEntry,
    CandidateModel,
    ProviderType,
    get_config_manager,
    get_config_manager_db,
)

# Agent configuration manager
from .agents_db import (
    AgentConfigManagerDB,
    get_agent_config_manager,
)

# Multi-process settings (v11)
from .settings import (
    WORKER_MODE,
    is_multi_process_mode,
    WorkerSettings,
    get_worker_settings,
    SSESettings,
    get_sse_settings,
    ENABLE_AUTO_SCALING,
    ENABLE_CRASH_RECOVERY,
    ENABLE_IDEMPOTENCY,
    # Context compaction (v12)
    ContextCompactionSettings,
    get_context_compaction_settings,
)

__all__ = [
    # Sync wrapper (backward compatible)
    'ConfigManager',
    'AppConfig', 
    'ApiKeyEntry',
    'CandidateModel',
    'ProviderType',
    'get_config_manager',
    # Async (primary, database-backed)
    'ConfigManagerDB',
    'get_config_manager_db',
    # Agent configuration
    'AgentConfigManagerDB',
    'get_agent_config_manager',
    # Multi-process settings (v11)
    'WORKER_MODE',
    'is_multi_process_mode',
    'WorkerSettings',
    'get_worker_settings',
    'SSESettings',
    'get_sse_settings',
    'ENABLE_AUTO_SCALING',
    'ENABLE_CRASH_RECOVERY',
    'ENABLE_IDEMPOTENCY',
    # Context compaction (v12)
    'ContextCompactionSettings',
    'get_context_compaction_settings',
]
