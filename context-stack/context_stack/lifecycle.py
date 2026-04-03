"""
Context Stack — Lifecycle Executor

The 6-step lifecycle that ALL skill types share:

  ① CHECKPOINT  — save context snapshot
  ② PRE-HOOKS   — inject skill prompt, setup tools
  ③ EXECUTE     — agent works (delegated to AgentExecutor)
  ④ POST-HOOKS  — collect metadata, validate
  ⑤ SUMMARIZE   — compress scope messages to structured summary
  ⑥ RELOAD      — replace raw messages with summary, save to memory

This is the ONLY execution path. Normal, Meta, and Recall skills
all go through these exact 6 steps. The difference is what happens
in each step (controlled by the skill's hooks and content).
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from .context.types import (
    CompactAction,
    CompactResult,
    LifecycleResult,
    Message,
    MessageRole,
    ScopeRecord,
    ScopeState,
)
from .context.checkpoint import CheckpointManager
from .context.summarizer import StructuredSummarizer
from .hooks import HookRegistry
from .skill.types import Skill, SkillType

logger = logging.getLogger("context_stack.lifecycle")


class LifecycleExecutor:
    """
    Executes the 6-step skill lifecycle.
    
    The executor is skill-type-agnostic — it runs the same 6 steps
    regardless of whether the skill is Normal, Meta, or Recall.
    """

    def __init__(
        self,
        checkpoint_mgr: CheckpointManager,
        summarizer: StructuredSummarizer,
        counter,
        store,
        hooks: HookRegistry,
    ):
        self._checkpoint = checkpoint_mgr
        self._summarizer = summarizer
        self._counter = counter
        self._store = store
        self._hooks = hooks
        self._active: bool = False  # Fix #5: re-entrant guard

    def run(
        self,
        skill: Skill,
        messages: List[Message],
        executor,                     # AgentExecutor protocol
        extra_tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LifecycleResult:
        """
        Run the full 6-step lifecycle.
        
        Args:
            skill: the Skill to execute (Normal, Meta, or Recall)
            messages: current conversation messages
            executor: AgentExecutor (host-provided agent loop)
            extra_tools: additional tools to inject (e.g., memory tools for Recall)
        
        Returns:
            LifecycleResult with compacted messages and scope metadata
        """
        # Fix #5: Guard against nested scope execution
        if self._active:
            raise RuntimeError(
                f"Cannot start scope '{skill.name}' while scope is already active. "
                f"Nested scopes are not supported — complete or abort the active scope first."
            )

        # Create scope record
        scope = ScopeRecord(
            name=skill.name,
            skill_name=skill.name if skill.skill_type != SkillType.META else "meta",
        )
        
        self._active = True
        try:
            # ─── ① CHECKPOINT ───
            self._checkpoint.checkpoint(scope, messages)
            logger.info("① CHECKPOINT: scope=%s skill=%s", scope.id, skill.name)

            # ─── ② PRE-HOOKS ───
            messages = self._pre_hooks(skill, scope, messages)
            logger.info("② PRE-HOOKS: prompt_injected=%s", bool(skill.prompt))

            # ─── ③ EXECUTE ───
            messages = self._execute(skill, scope, messages, executor, extra_tools)
            logger.info("③ EXECUTE: messages=%d", len(messages))

            # ─── ④ POST-HOOKS ───
            self._post_hooks(skill, scope, messages)
            logger.info("④ POST-HOOKS: complete")

            # ─── ⑤ SUMMARIZE ───
            scope_messages = messages[scope.message_start_idx:]
            summary_text = self._summarizer.summarize(scope, scope_messages)
            scope.summary = summary_text
            scope.ended_at = time.time()
            logger.info("⑤ SUMMARIZE: len=%d", len(summary_text))

            # ─── ⑥ RELOAD ───
            summary_msg = Message(
                role=MessageRole.ASSISTANT,
                content=summary_text,
                metadata={
                    "scope_id": scope.id,
                    "scope_name": scope.name,
                    "skill_type": skill.skill_type.value,
                    "compacted": True,
                },
            )
            summary_msg.token_count = self._counter.count(summary_text)
            
            new_messages = self._checkpoint.reload(scope, messages, summary_msg)
            self._store.save(scope)
            logger.info(
                "⑥ RELOAD: scope=%s tokens_saved=%d",
                scope.id, scope.tokens_saved,
            )

            compact = CompactResult(
                action=CompactAction.SCOPE,
                messages=new_messages,
                tokens_before=scope.tokens_before + self._counter.count_messages(scope_messages),
                tokens_after=scope.tokens_after,
                tokens_saved=scope.tokens_saved,
                scope_id=scope.id,
                summary=summary_text,
            )

            return LifecycleResult(
                messages=new_messages,
                scope=scope,
                compact=compact,
                skill_name=skill.name,
                success=True,
            )

        except Exception as e:
            logger.error("Lifecycle failed for skill '%s': %s", skill.name, e)
            scope.errors.append(str(e))
            scope.ended_at = time.time()
            
            return LifecycleResult(
                messages=messages,
                scope=scope,
                compact=CompactResult(action=CompactAction.SKIP, messages=messages),
                skill_name=skill.name,
                success=False,
                error=str(e),
            )
        finally:
            self._active = False  # Fix #5: always release

    # ─────────────────────────────────────────
    # Step implementations
    # ─────────────────────────────────────────

    def _pre_hooks(
        self,
        skill: Skill,
        scope: ScopeRecord,
        messages: List[Message],
    ) -> List[Message]:
        """② PRE-HOOKS: Inject skill prompt + run registered hooks."""
        # Inject skill prompt
        prompt = skill.build_prompt()
        if prompt:
            skill_msg = Message(
                role=MessageRole.SYSTEM,
                content=prompt,
                metadata={"skill_prompt": True, "skill_name": skill.name},
            )
            messages = messages + [skill_msg]
        
        # Run skill-specific pre-hooks
        for hook_fn in skill.pre_hooks:
            try:
                messages = hook_fn(scope, messages)
            except Exception as e:
                logger.warning("Skill pre-hook failed: %s", e)
        
        # Run global pre-hooks
        messages = self._hooks.run_pre_hooks(scope, messages)
        
        return messages

    def _execute(
        self,
        skill: Skill,
        scope: ScopeRecord,
        messages: List[Message],
        executor,
        extra_tools: Optional[List[Dict[str, Any]]],
    ) -> List[Message]:
        """③ EXECUTE: Run the agent loop via AgentExecutor."""
        return executor.execute(
            messages=messages,
            extra_tools=extra_tools,
        )

    def _post_hooks(
        self,
        skill: Skill,
        scope: ScopeRecord,
        messages: List[Message],
    ) -> None:
        """④ POST-HOOKS: Run hooks, collect metadata."""
        # Run skill-specific post-hooks
        for hook_fn in skill.post_hooks:
            try:
                hook_fn(scope, messages)
            except Exception as e:
                logger.warning("Skill post-hook failed: %s", e)
        
        # Run global post-hooks
        self._hooks.run_post_hooks(scope, messages)
