"""
Worker Module

Implements the unified Worker model for the Master-driven architecture (v12).
Workers execute single tasks (think or execute) and return results.

v12: Master-driven architecture:
     - Workers are truly stateless (single task execution)
     - Master manages Runtime lifecycle and drives ReACT loops
     - Workers receive context from Master, execute task, return result

Communication:
- Workers call LLM APIs directly (not through Gateway)
- Workers call MCP servers directly (not through Gateway)
- Workers use Gateway API for:
  - Task claiming (/api/claim/*)
  - Result submission (/api/result/*)
  - Idempotency checks (/api/mcp/execution/*)
  - Chat broadcast (/api/chat/event)
"""

from .worker import Worker, WorkerConfig, run_worker
from .id_generator import IDGenerator, RoundTracker
from .llm_caller import LLMCaller, ActionType, AgentAction, ThinkingResult
from .think_handler import handle_think

__all__ = [
    "Worker",
    "WorkerConfig",
    "run_worker",
    "IDGenerator",
    "RoundTracker",
    "LLMCaller",
    "ActionType",
    "AgentAction",
    "ThinkingResult",
    "handle_think",
]
