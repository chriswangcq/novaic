"""数据库状态值枚举定义"""

from enum import Enum


class RuntimePhase(str, Enum):
    NEED_THINK = "need_think"
    WAITING_ACTIONS = "waiting_actions"
    QUEUED = "queued"
    THINKING = "thinking"
    TOOL_CALLING = "tool_calling"
    WAITING_TOOLS = "waiting_tools"
    REST = "rest"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class RuntimeStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskState(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SagaState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


class SubagentStatus(str, Enum):
    SLEEPING = "sleeping"
    AWAKE = "awake"
    SUMMARIZING = "summarizing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ExecutionLogType(str, Enum):
    SYSTEM = "system"
    THINK = "think"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    USER = "user"
