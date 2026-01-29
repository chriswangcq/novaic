"""
NovAIC Agent - Agent Runtime Module

This module contains the agent functionality:
- agent/core: State management (AgentState, StateManager)
- agent/events: Event-driven architecture (EventBus, handlers, adapters)
- agent/session: Session management (persistence, compaction)
- agent/subagent: Sub-agent system for parallel task execution
- agent/wake: Wake-up system (triggers, controller)
- agent/micro: Micro Agent system (rules, LLM-based evaluation)

Note: NovAICAgent implementation is in core/agent.py
      Import directly: from core.agent import NovAICAgent
"""

# Only export state management from agent package
# NovAICAgent is in core/agent.py to avoid circular imports
from .core.state import AgentState, StateManager

__all__ = ["AgentState", "StateManager"]
