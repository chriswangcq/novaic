"""
Context Stack — Engine

The unified facade. Single entry point for all operations.

    engine.run()         — run a skill through the full lifecycle
    engine.run_meta()    — run Meta Skill (no matching skill)
    engine.run_recall()  — run Recall Skill (memory exploration)
    engine.match()       — match a task to a skill
    engine.status()      — inspect context state
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

from .context.types import (
    CompactAction,
    CompactConfig,
    CompactResult,
    LifecycleResult,
    Message,
    StackStatus,
)
from .context.checkpoint import CheckpointManager
from .context.summarizer import StructuredSummarizer
from .context.compact import micro_compact
from .context.compact.auto import AutoCompactor
from .hooks import HookRegistry
from .lifecycle import LifecycleExecutor
from .memory.store import MemoryScopeStore
from .skill.types import Skill, SkillType
from .skill.registry import SkillRegistry
from .skill.builtins.meta import MetaSkill
from .skill.builtins.recall import RecallSkill
from .tool_router import RecallToolRouter

logger = logging.getLogger("context_stack")


class ContextEngine:
    """
    The unified Context + Memory + Skill engine.
    
    Core insight: Skill execution lifecycle IS context management IS memory management.
    They are three views of the same process.
    
    Host provides:
        executor:   how to run the agent loop (AgentExecutor protocol)
        summarizer: how to call LLM for summarization (Summarizer protocol)
        counter:    how to count tokens (TokenCounter protocol)
        store:      where to persist scopes (MemoryBackend protocol, optional)
    
    Engine provides:
        run():         full 6-step lifecycle for any skill
        run_meta():    scoped execution without a skill
        run_recall():  memory exploration with tools
        match():       find the right skill for a task
        status():      context budget + scope history
    """

    def __init__(
        self,
        executor,                     # AgentExecutor protocol
        summarizer,                   # Summarizer protocol
        counter,                      # TokenCounter protocol
        config: Optional[CompactConfig] = None,
        store=None,                   # MemoryBackend / MemoryScopeStore
    ):
        self._executor = executor
        self._summarizer = summarizer
        self._counter = counter
        self._config = config or CompactConfig()
        self._store = store or MemoryScopeStore()
        
        # Sub-components
        self._hooks = HookRegistry()
        self._checkpoint = CheckpointManager(counter, self._config)  # Fix #4/#6: pass config
        self._structured_summarizer = StructuredSummarizer(
            summarizer, counter, self._config.auto_summary_max_tokens,
        )
        self._lifecycle = LifecycleExecutor(
            checkpoint_mgr=self._checkpoint,
            summarizer=self._structured_summarizer,
            counter=self._counter,
            store=self._store,
            hooks=self._hooks,
        )
        self._auto_compactor = AutoCompactor(
            self._config, summarizer, counter,
        )
        self._registry = SkillRegistry()
        self._recall_skill = RecallSkill(self._store, self._counter)
        
        # Stats (Fix #7: thread-safe)
        self._stats_lock = threading.Lock()
        self._total_tokens_saved = 0
        self._total_lifecycles = 0

    # ═════════════════════════════════════════
    # Core API 1: run() — Execute a skill
    # ═════════════════════════════════════════

    def run(
        self,
        skill: Skill,
        messages: List[Message],
        task: str = "",
    ) -> LifecycleResult:
        """
        Run a skill through the full 6-step lifecycle.
        
        checkpoint → pre_hooks → execute → post_hooks → summarize → reload
        
        Args:
            skill:    Skill to execute
            messages: current conversation
            task:     user's request text (for metadata)
        
        Returns:
            LifecycleResult with compacted messages and scope data
        """
        # Determine extra tools and executor (Fix #3: auto-wrap for Recall)
        extra_tools = None
        executor = self._executor
        if skill.skill_type == SkillType.RECALL:
            extra_tools = self._recall_skill.get_tool_definitions()
            # Fix #3: Wrap executor with RecallToolRouter for transparent tool dispatch
            executor = RecallToolRouter(self._executor, self._recall_skill)
        
        result = self._lifecycle.run(
            skill=skill,
            messages=messages,
            executor=executor,
            extra_tools=extra_tools,
        )
        
        if result.success:
            with self._stats_lock:  # Fix #7
                self._total_tokens_saved += result.compact.tokens_saved
                self._total_lifecycles += 1
        
        return result

    # ═════════════════════════════════════════
    # Core API 2: run_meta() — Scoped execution without skill
    # ═════════════════════════════════════════

    def run_meta(
        self,
        messages: List[Message],
        task: str = "",
        name: str = "",
    ) -> LifecycleResult:
        """
        Run a Meta Skill — scope wrapper for unmatched tasks.
        
        Same lifecycle, but no prompt/workflow injection.
        Ensures every user request is under a scope.
        """
        skill = MetaSkill.create(name=name, task=task)
        return self.run(skill, messages, task)

    # ═════════════════════════════════════════
    # Core API 3: run_recall() — Memory exploration
    # ═════════════════════════════════════════

    def run_recall(
        self,
        messages: List[Message],
        query: str = "",
    ) -> LifecycleResult:
        """
        Run a Recall Skill — inject memory tools, let agent explore.
        
        Pre-hooks inject memory_expand and memory_search tools.
        Agent uses them to progressively explore past scope records.
        Post-hooks remove the temporary tools.
        
        The recall itself goes through the full lifecycle →
        the exploration + follow-up work is all summarized and reloaded.
        """
        skill = self._recall_skill.create(query=query)
        return self.run(skill, messages)

    # ═════════════════════════════════════════
    # Core API 4: match() — Skill matching
    # ═════════════════════════════════════════

    def match(
        self,
        task: str,
        agent_id: str = "",
        file_paths: Optional[List[str]] = None,
    ) -> Optional[Skill]:
        """
        Match a task to the best skill in the registry.
        Returns None if no match (caller should use run_meta).
        """
        return self._registry.match(task, agent_id, file_paths)

    def match_and_run(
        self,
        messages: List[Message],
        task: str,
        agent_id: str = "",
        file_paths: Optional[List[str]] = None,
    ) -> LifecycleResult:
        """
        Convenience: match + run in one call.
        Falls back to Meta Skill if no match.
        """
        skill = self.match(task, agent_id, file_paths)
        if skill:
            return self.run(skill, messages, task)
        else:
            return self.run_meta(messages, task=task)

    # ═════════════════════════════════════════
    # Core API 5: status()
    # ═════════════════════════════════════════

    def status(self, messages: Optional[List[Message]] = None) -> StackStatus:
        """Get current engine status."""
        used = self._counter.count_messages(messages) if messages else 0
        budget = self._config.context_window
        
        recallable = (
            self._store.get_recallable_names()
            if hasattr(self._store, 'get_recallable_names')
            else []
        )
        
        return StackStatus(
            used_tokens=used,
            budget_tokens=budget,
            usage_ratio=used / budget if budget > 0 else 0,
            total_scopes=self._store.count if hasattr(self._store, 'count') else 0,
            compacted_scopes=self._store.compacted_count if hasattr(self._store, 'compacted_count') else 0,
            recall_available=recallable,
            total_tokens_saved=self._total_tokens_saved,
            total_compactions=self._total_lifecycles,
        )

    # ═════════════════════════════════════════
    # Recall Tool Dispatch
    # ═════════════════════════════════════════

    def handle_recall_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Handle a recall tool call from the agent.
        
        Called by the host when the agent invokes memory_expand or memory_search.
        The host's AgentExecutor should route these tool calls here.
        """
        return self._recall_skill.execute_tool(tool_name, args)

    # ═════════════════════════════════════════
    # Background Compaction (between scopes)
    # ═════════════════════════════════════════

    def maybe_compact(self, messages: List[Message]) -> CompactResult:
        """
        Run background compaction pipeline (Micro → Auto).
        Call between turns when NOT inside a lifecycle.
        """
        messages = micro_compact(messages, self._config)
        
        if self._auto_compactor.should_trigger(messages):
            result = self._auto_compactor.compact(messages)
            if result.action != CompactAction.SKIP:
                with self._stats_lock:  # Fix #7
                    self._total_tokens_saved += result.tokens_saved
                    self._total_lifecycles += 1
            return result
        
        tokens = self._counter.count_messages(messages)
        return CompactResult(
            action=CompactAction.MICRO,
            messages=messages,
            tokens_before=tokens,
            tokens_after=tokens,
        )

    def emergency_compact(self, messages: List[Message]) -> CompactResult:
        """Emergency compaction for prompt_too_long errors."""
        result = self._auto_compactor.emergency_compact(messages)
        with self._stats_lock:  # Fix #7
            self._total_tokens_saved += result.tokens_saved
        return result

    # ═════════════════════════════════════════
    # Registry & Hooks access
    # ═════════════════════════════════════════

    @property
    def registry(self) -> SkillRegistry:
        """Access the skill registry to register/list skills."""
        return self._registry

    @property
    def hooks(self) -> HookRegistry:
        """Access the hook registry to register pre/post hooks."""
        return self._hooks

    @property
    def recall(self) -> RecallSkill:
        """Access the RecallSkill for direct tool execution."""
        return self._recall_skill

    def list_scopes(self) -> List[dict]:
        """List all scopes available for recall."""
        records = self._store.list_all(limit=50)
        return [
            {
                "id": r.id,
                "name": r.name,
                "skill": r.skill_name,
                "files": r.files_changed[:5],
                "tools": sum(r.tools_used.values()),
                "duration": f"{r.duration_seconds:.0f}s",
                "tokens_saved": r.tokens_saved,
                "has_raw": bool(r.raw_messages),
            }
            for r in records
        ]
