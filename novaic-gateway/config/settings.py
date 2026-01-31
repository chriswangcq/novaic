"""
Multi-process Architecture Settings

Configuration for the v11 multi-process Worker architecture.

v11: Created for multi-process architecture.
"""

import os
from dataclasses import dataclass
from typing import Optional


# ==================== Mode Configuration ====================

# v11: Multi-process mode is now the default and only mode
# Single-process mode has been removed
WORKER_MODE = "multi"

def is_multi_process_mode() -> bool:
    """Check if running in multi-process mode. Always returns True in v11."""
    return True


# ==================== Worker Configuration ====================

@dataclass
class WorkerSettings:
    """Settings for Worker processes."""
    
    # Process counts
    min_workers: int = 2
    max_workers: int = 5
    
    # Per-worker concurrency
    max_concurrent_per_worker: int = 10
    
    # Timeouts (seconds)
    heartbeat_timeout: int = 60
    task_timeout_minutes: int = 5
    
    # Auto-scaling
    scale_up_threshold: int = 10
    scale_down_threshold: int = 2
    scale_cooldown: int = 60
    
    # Health check
    health_check_interval: int = 30
    recovery_interval: int = 60


def get_worker_settings() -> WorkerSettings:
    """Get Worker settings from environment or defaults."""
    return WorkerSettings(
        min_workers=int(os.environ.get("NOVAIC_MIN_WORKERS", "2")),
        max_workers=int(os.environ.get("NOVAIC_MAX_WORKERS", "5")),
        max_concurrent_per_worker=int(os.environ.get("NOVAIC_MAX_CONCURRENT", "10")),
        heartbeat_timeout=int(os.environ.get("NOVAIC_HEARTBEAT_TIMEOUT", "60")),
        task_timeout_minutes=int(os.environ.get("NOVAIC_TASK_TIMEOUT", "5")),
    )


# ==================== SSE Configuration ====================

@dataclass
class SSESettings:
    """Settings for SSE broadcast."""
    
    heartbeat_interval: int = 30
    queue_max_size: int = 100


def get_sse_settings() -> SSESettings:
    """Get SSE settings from environment or defaults."""
    return SSESettings(
        heartbeat_interval=int(os.environ.get("NOVAIC_SSE_HEARTBEAT", "30")),
        queue_max_size=int(os.environ.get("NOVAIC_SSE_QUEUE_SIZE", "100")),
    )


# ==================== Feature Flags ====================

# Enable/disable specific features
ENABLE_AUTO_SCALING = os.environ.get("NOVAIC_ENABLE_AUTO_SCALING", "true").lower() == "true"
ENABLE_CRASH_RECOVERY = os.environ.get("NOVAIC_ENABLE_CRASH_RECOVERY", "true").lower() == "true"
ENABLE_IDEMPOTENCY = os.environ.get("NOVAIC_ENABLE_IDEMPOTENCY", "true").lower() == "true"


# ==================== Logging ====================

# Log level for multi-process components
WORKER_LOG_LEVEL = os.environ.get("NOVAIC_WORKER_LOG_LEVEL", "INFO")
