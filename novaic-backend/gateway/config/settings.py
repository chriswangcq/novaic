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


# ==================== Context Compaction Settings ====================

@dataclass
class ContextCompactionSettings:
    """Settings for LLM-based context compaction."""
    
    # Model to use for compaction (fast, cheap model preferred)
    compaction_model: str = "moonshot-v1-8k"
    
    # Threshold: compact when context exceeds this ratio of model's limit (80%)
    compaction_threshold_ratio: float = 0.8
    
    # Target: compact to this ratio of model's limit (30%)
    compaction_target_ratio: float = 0.3
    
    # Minimum messages to keep (not compacted)
    min_messages_to_keep: int = 5
    
    # System prompt for compaction
    compaction_prompt: str = """你是一个对话压缩专家。你的任务是将一段较长的对话历史压缩成简洁的摘要，保留所有关键信息。

## 压缩要求

1. **保留关键信息**：
   - 用户的核心需求和目标
   - 已完成的重要操作和结果
   - 关键决策和上下文
   - 重要的文件路径、变量名、配置值等

2. **删除冗余内容**：
   - 重复的问答
   - 已解决的中间调试步骤
   - 不影响后续对话的细节

3. **输出格式**：
   - 使用简洁的 bullet points
   - 按时间顺序或主题组织
   - 保持客观，不添加解释

## 输入格式

你将收到一段对话历史，格式为 JSON 数组，每个元素包含 role 和 content。

## 输出格式

直接输出压缩后的摘要文本，不要包含任何额外的解释或标记。"""


def get_context_compaction_settings() -> ContextCompactionSettings:
    """Get context compaction settings from environment or defaults."""
    return ContextCompactionSettings(
        compaction_model=os.environ.get("NOVAIC_COMPACTION_MODEL", "moonshot-v1-8k"),
        compaction_threshold_ratio=float(os.environ.get("NOVAIC_COMPACTION_THRESHOLD", "0.8")),
        compaction_target_ratio=float(os.environ.get("NOVAIC_COMPACTION_TARGET", "0.3")),
        min_messages_to_keep=int(os.environ.get("NOVAIC_MIN_MESSAGES_KEEP", "5")),
    )
