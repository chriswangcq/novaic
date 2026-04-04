"""
Context Stack v2 — Hook Registry

Pre-hooks and post-hooks for skill execution lifecycle.
Hooks are extension points — they do NOT control the lifecycle,
they participate in it.

Adapted for v2:
  - Same hook signatures as v1
  - Added skill_end validator integration
  - Hooks operate on scope phase transitions
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from .types import Message, ScopeRecord

logger = logging.getLogger("context_stack.v2.hooks")

# Hook signatures
# pre_hook(scope, messages) -> messages (can modify)
# post_hook(scope, messages) -> None (observe only)
PreHook = Callable[[ScopeRecord, List[Message]], List[Message]]
PostHook = Callable[[ScopeRecord, List[Message]], None]


class HookRegistry:
    """
    Manages pre/post hooks for the lifecycle.

    Hooks run in registration order (by priority, lower = earlier).
    Pre-hooks can modify messages (e.g., inject prompts).
    Post-hooks are observers (e.g., logging, metrics).
    """

    def __init__(self):
        self._pre_hooks: List[tuple] = []   # (name, fn, priority)
        self._post_hooks: List[tuple] = []

    def register_pre(
        self,
        name: str,
        fn: PreHook,
        priority: int = 100,
    ) -> None:
        """Register a pre-hook. Lower priority = runs earlier."""
        self._pre_hooks.append((name, fn, priority))
        self._pre_hooks.sort(key=lambda x: x[2])

    def register_post(
        self,
        name: str,
        fn: PostHook,
        priority: int = 100,
    ) -> None:
        """Register a post-hook. Lower priority = runs earlier."""
        self._post_hooks.append((name, fn, priority))
        self._post_hooks.sort(key=lambda x: x[2])

    def run_pre_hooks(
        self,
        scope: ScopeRecord,
        messages: List[Message],
    ) -> List[Message]:
        """Run all pre-hooks, passing messages through each."""
        for name, fn, _ in self._pre_hooks:
            try:
                messages = fn(scope, messages)
            except Exception as e:
                logger.error("Pre-hook '%s' failed: %s", name, e)
        return messages

    def run_post_hooks(
        self,
        scope: ScopeRecord,
        messages: List[Message],
    ) -> None:
        """Run all post-hooks as observers."""
        for name, fn, _ in self._post_hooks:
            try:
                fn(scope, messages)
            except Exception as e:
                logger.error("Post-hook '%s' failed: %s", name, e)

    def unregister(self, name: str) -> None:
        """Remove all hooks with the given name."""
        self._pre_hooks = [h for h in self._pre_hooks if h[0] != name]
        self._post_hooks = [h for h in self._post_hooks if h[0] != name]

    def clear(self) -> None:
        """Remove all hooks."""
        self._pre_hooks.clear()
        self._post_hooks.clear()

    @property
    def pre_hook_count(self) -> int:
        return len(self._pre_hooks)

    @property
    def post_hook_count(self) -> int:
        return len(self._post_hooks)
