"""
Context Stack v2 — NovAIC Runtime Adapter (§8.2)

Bridges context-stack v2 engine to NovAIC runtime components:
  - SkillRegistry → engine._registry for skill_begin resolution
  - compact_engine.SkillScopedCompactor (v1) → replaced by v2 engine
  - Message format conversion (NovAIC ↔ v2)
  - Factory: create_engine_for_novaic()

This module is the single entry point for NovAIC integration.
NovAIC runtime should:
  1. Call create_engine_for_novaic() at session start
  2. Use engine.router for tool dispatch in the agent loop
  3. Use engine.prepare_messages_for_llm() before each LLM call
  4. Call engine.close() at session end

§8.2 挂载点:
  - Task Worker: pull_turn_context → LLM/tool → push_turn
  - Chat / 同步 Runtime: router.dispatch in the agent loop
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from .config import CompactConfig
from .engine import ContextEngine
from .types import Message, MessageRole

logger = logging.getLogger("context_stack.v2.novaic_adapter")


# ─────────────────────────────────────────────
# Message format conversion
# ─────────────────────────────────────────────

def novaic_msg_to_v2(msg: Any) -> Message:
    """
    Convert a NovAIC Message (dict or object) to v2 Message.

    NovAIC messages are typically dicts with:
      - role: str ("system", "user", "assistant", "tool")
      - content: str
      - tool_name: str (optional)
      - tool_input: str (optional)
      - metadata: dict (optional)
    """
    if isinstance(msg, Message):
        return msg

    if isinstance(msg, dict):
        role_str = msg.get("role", "user")
        return Message(
            role=MessageRole(role_str),
            content=msg.get("content", ""),
            tool_name=msg.get("tool_name") or msg.get("name"),
            tool_input=msg.get("tool_input"),
            tool_call_id=msg.get("tool_call_id") or msg.get("id"),
            token_count=msg.get("token_count"),
            timestamp=msg.get("timestamp", 0),
            metadata=msg.get("metadata", {}),
        )

    # Object-style (duck-typed NovAIC message)
    role_str = getattr(msg, "role", "user")
    if isinstance(role_str, str):
        role = MessageRole(role_str)
    elif hasattr(role_str, "value"):
        role = MessageRole(role_str.value)
    else:
        role = MessageRole.USER

    return Message(
        role=role,
        content=getattr(msg, "content", ""),
        tool_name=getattr(msg, "tool_name", None) or getattr(msg, "name", None),
        tool_input=getattr(msg, "tool_input", None),
        tool_call_id=getattr(msg, "tool_call_id", None) or getattr(msg, "id", None),
        token_count=getattr(msg, "token_count", None),
        timestamp=getattr(msg, "timestamp", 0),
        metadata=getattr(msg, "metadata", {}),
    )


def v2_msg_to_novaic(msg: Message) -> Dict[str, Any]:
    """
    Convert a v2 Message back to NovAIC-compatible dict.

    Returns a clean dict suitable for NovAIC runtime consumption.
    """
    d = {
        "role": msg.role.value,
        "content": msg.content,
    }
    if msg.tool_name:
        d["tool_name"] = msg.tool_name
    if msg.tool_input:
        d["tool_input"] = msg.tool_input
    if msg.tool_call_id:
        d["tool_call_id"] = msg.tool_call_id
    if msg.token_count is not None:
        d["token_count"] = msg.token_count
    if msg.metadata:
        d["metadata"] = msg.metadata
    return d


def convert_messages(msgs: List[Any]) -> List[Message]:
    """Batch convert NovAIC messages to v2."""
    return [novaic_msg_to_v2(m) for m in msgs]


def export_messages(msgs: List[Message]) -> List[Dict[str, Any]]:
    """Batch convert v2 messages back to NovAIC dicts."""
    return [v2_msg_to_novaic(m) for m in msgs]


# ─────────────────────────────────────────────
# SkillRegistry adapter
# ─────────────────────────────────────────────

class SkillRegistryAdapter:
    """
    Adapts NovAIC SkillRegistry to the interface expected by v2 engine.

    The v2 engine ToolRouter does:
        registry.get(skill_name) → skill object
        skill.build_prompt() → str
        skill.skill_type → enum

    This adapter maps NovAIC SkillRegistry's get_by_name() to that.
    """

    def __init__(self, novaic_registry: Any):
        """
        Args:
            novaic_registry: NovAIC SkillRegistry instance
        """
        self._registry = novaic_registry

    def get(self, name: str) -> Optional[Any]:
        """Look up a skill by name."""
        skill = self._registry.get_by_name(name)
        if skill is None:
            return None

        # Wrap to provide expected interface
        return _SkillWrapper(skill)


class _SkillWrapper:
    """Wraps a NovAIC Skill object to provide the v2-expected interface."""

    def __init__(self, skill: Any):
        self._skill = skill

    def build_prompt(self) -> Optional[str]:
        """Build the skill prompt (Layer 2 body)."""
        if hasattr(self._skill, 'body') and self._skill.body:
            parts = []
            if self._skill.body.prompt:
                parts.append(self._skill.body.prompt)
            if self._skill.body.workflow:
                parts.append(f"\n## Workflow\n{self._skill.body.workflow}")
            return "\n".join(parts) if parts else None
        return None

    @property
    def skill_type(self):
        """Return a SkillType-like object with .value."""
        meta = getattr(self._skill, 'metadata', None)
        if meta and hasattr(meta, 'category'):
            return _ValueWrapper(meta.category or "normal")
        return _ValueWrapper("normal")

    @property
    def name(self) -> str:
        return getattr(self._skill, 'name', '')


class _ValueWrapper:
    """Simple wrapper to provide .value attribute."""
    def __init__(self, value: str):
        self.value = value


# ─────────────────────────────────────────────
# Summarizer adapter
# ─────────────────────────────────────────────

class NovAICSummarizerAdapter:
    """
    Adapts a NovAIC LLM client to the Summarizer protocol.

    The v2 Summarizer protocol expects:
        summarize(messages, max_tokens, instructions) → str

    This adapter calls the NovAIC LLM client to produce summaries.
    """

    def __init__(self, llm_client: Any, model: str = ""):
        self._client = llm_client
        self._model = model

    def summarize(
        self,
        messages: List[Message],
        max_tokens: int = 2000,
        instructions: str = "",
    ) -> str:
        """Summarize messages using the NovAIC LLM client."""
        # Convert messages to text for summarization
        text_parts = []
        for msg in messages:
            role = msg.role.value.upper()
            tool_tag = f" [{msg.tool_name}]" if msg.tool_name else ""
            text_parts.append(f"[{role}{tool_tag}]: {msg.content[:500]}")

        content = "\n".join(text_parts)

        prompt = (
            f"{instructions}\n\n"
            f"Please summarize the following conversation:\n\n{content}"
        )

        try:
            # Try common NovAIC client interfaces
            if hasattr(self._client, 'generate'):
                result = self._client.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    model=self._model,
                )
                return result if isinstance(result, str) else str(result)

            if hasattr(self._client, 'complete'):
                result = self._client.complete(prompt, max_tokens=max_tokens)
                return result if isinstance(result, str) else str(result)

            # Fallback: just truncate
            logger.warning(
                "LLM client has no known generation method, using truncation."
            )
            return content[:max_tokens * 4]

        except Exception as e:
            logger.error("LLM summarization failed: %s", e)
            return content[:max_tokens * 4]


# ─────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────

def create_engine_for_novaic(
    *,
    # Core
    context_window: int = 200_000,
    compact_threshold: float = 0.70,
    emergency_threshold: float = 0.95,

    # Persistence
    db_path: Optional[str] = None,
    store_raw_messages: bool = True,

    # Integration
    skill_registry: Optional[Any] = None,
    llm_client: Optional[Any] = None,
    llm_model: str = "",
    counter: Optional[Any] = None,
    report_validator: Optional[Any] = None,

    # Behavior
    auto_meta: bool = True,
    max_skill_depth: int = 4,

    # Extra config overrides
    **config_kwargs,
) -> ContextEngine:
    """
    Create a ContextEngine configured for NovAIC runtime.

    This is the recommended entry point for NovAIC integration.

    Example:
        engine = create_engine_for_novaic(
            context_window=200_000,
            db_path="./session_scopes.db",
            skill_registry=my_registry,
            llm_client=my_llm,
        )

        # In agent loop:
        msgs = engine.prepare_messages_for_llm(messages)
        extra_tools = engine.router.get_tool_definitions()
        response = llm.call(msgs, tools=tools + extra_tools)

        for tool_call in response.tool_calls:
            if engine.router.is_engine_tool(tool_call.name):
                result = engine.router.dispatch(
                    tool_call.name, tool_call.args, msgs,
                )
                msgs = result.messages
                # Append TOOL response to messages
            else:
                # Handle business tool normally
                ...

        engine.close()

    Args:
        context_window: LLM context window size in tokens
        compact_threshold: usage ratio to trigger compaction (0-1)
        emergency_threshold: usage ratio for emergency compaction
        db_path: SQLite DB path for persistent scopes (None = in-memory)
        store_raw_messages: whether to store raw messages in DB
        skill_registry: NovAIC SkillRegistry instance (optional)
        llm_client: NovAIC LLM client for summarization (optional)
        llm_model: model name for LLM summarization
        counter: TokenCounter implementation (optional)
        report_validator: SkillEndReportValidator (optional)
        auto_meta: auto-create meta scope when stack empty
        max_skill_depth: maximum nested skill depth
        **config_kwargs: additional CompactConfig overrides

    Returns:
        Configured ContextEngine instance
    """
    # Build config
    config = CompactConfig(
        context_window=context_window,
        compact_threshold=compact_threshold,
        emergency_threshold=emergency_threshold,
        auto_meta_when_stack_empty=auto_meta,
        max_skill_depth=max_skill_depth,
        scope_store_raw=store_raw_messages,
        **config_kwargs,
    )

    # Build store
    store = None
    if db_path:
        from .sqlite_store import SqliteScopeStore
        store = SqliteScopeStore(
            path=db_path,
            store_raw_messages=store_raw_messages,
        )

    # Build summarizer
    summarizer = None
    if llm_client:
        summarizer = NovAICSummarizerAdapter(llm_client, llm_model)

    # Build registry adapter
    registry = None
    if skill_registry:
        registry = SkillRegistryAdapter(skill_registry)

    engine = ContextEngine(
        config=config,
        store=store,
        summarizer=summarizer,
        counter=counter,
        report_validator=report_validator,
        registry=registry,
    )

    logger.info(
        "NovAIC engine created: window=%d store=%s registry=%s",
        context_window,
        "sqlite" if db_path else "memory",
        "yes" if skill_registry else "no",
    )

    return engine
