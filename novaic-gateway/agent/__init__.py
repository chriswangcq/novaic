"""
NovAIC Agent - Agent Runtime Module

This module contains the core agent functionality:
- agent/core: Agent core logic (ReAct loop, state management, LLM client)
- agent/events: Event-driven architecture (EventBus, handlers, adapters)
- agent/session: Session management (persistence, compaction)
- agent/subagent: Sub-agent system for parallel task execution
- agent/wake: Wake-up system (triggers, controller)
- agent/micro: Micro Agent system (rules, LLM-based evaluation)
"""

from .core.agent import NovAICAgent
from .core.state import AgentState, StateManager

__all__ = ["NovAICAgent", "AgentState", "StateManager"]
