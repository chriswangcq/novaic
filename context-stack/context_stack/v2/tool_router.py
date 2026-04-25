"""
Context Stack v2 — Skill Tool Router

The bridge between LLM tool_calls and the engine's internal scope management.

Handles four tool names:
  - skill_begin  → engine._begin_scope
  - skill_end    → engine._end_scope
  - memory_search → recall.execute_tool
  - memory_expand → recall.execute_tool

Also provides get_tool_definitions() for injection into LLM extra_tools.

§4.6.1, §4.6.5: skill_* and memory_* are "engine-parsed tools" that must be
executed in a fixed order within a single react_actions batch:
  1. recall tools (memory_*)
  2. skill tools (skill_begin/end)
  3. business tools (everything else)
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .types import Message, MessageRole

if TYPE_CHECKING:
    from .engine import ContextEngine

logger = logging.getLogger("context_stack.v2.tool_router")

# All engine-managed tool names
SKILL_TOOL_NAMES = frozenset({"skill_begin", "skill_end"})
RECALL_TOOL_NAMES = frozenset({"memory_expand", "memory_search"})
ENGINE_TOOL_NAMES = SKILL_TOOL_NAMES | RECALL_TOOL_NAMES


class SkillToolRouter:
    """
    Routes engine tool calls from the LLM to the appropriate engine methods.

    Usage:
        router = SkillToolRouter(engine)

        # Get tool definitions to inject into LLM extra_tools
        extra_tools = router.get_tool_definitions()

        # After LLM responds with tool_calls, dispatch them:
        for tool_call in tool_calls:
            if router.is_engine_tool(tool_call.name):
                result = router.dispatch(tool_call.name, tool_call.args, messages)
                # Append TOOL response message
    """

    def __init__(self, engine: "ContextEngine"):
        self._engine = engine

    # ─────────────────────────────────────────
    # Tool Definitions (for LLM extra_tools)
    # ─────────────────────────────────────────

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Return all engine tool definitions for injection into LLM.

        Returns skill_begin, skill_end, and (optionally) memory tools.
        """
        tools = [
            self._skill_begin_schema(),
            self._skill_end_schema(),
        ]

        # Add recall tools if store has data or recall is enabled
        recall = self._engine._recall
        if recall:
            tools.extend(recall.get_tool_definitions())

        return tools

    def get_skill_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return only skill_begin/skill_end schemas (no recall)."""
        return [
            self._skill_begin_schema(),
            self._skill_end_schema(),
        ]

    # ─────────────────────────────────────────
    # Dispatch
    # ─────────────────────────────────────────

    def is_engine_tool(self, tool_name: str) -> bool:
        """Check if a tool name is managed by the engine."""
        return tool_name in ENGINE_TOOL_NAMES

    def dispatch(
        self,
        tool_name: str,
        args: Dict[str, Any],
        messages: List[Message],
    ) -> "ToolResult":
        """
        Dispatch a tool call to the appropriate engine method.

        Args:
            tool_name: the tool being called
            args:      parsed arguments from the LLM
            messages:  current conversation messages

        Returns:
            ToolResult with the response content and updated messages
        """
        if tool_name == "skill_begin":
            return self._handle_skill_begin(args, messages)
        elif tool_name == "skill_end":
            return self._handle_skill_end(args, messages)
        elif tool_name in RECALL_TOOL_NAMES:
            return self._handle_recall(tool_name, args, messages)
        else:
            return ToolResult(
                content=f"Unknown engine tool: {tool_name}",
                messages=messages,
                success=False,
            )

    # ─────────────────────────────────────────
    # Handlers
    # ─────────────────────────────────────────

    def _handle_skill_begin(
        self,
        args: Dict[str, Any],
        messages: List[Message],
    ) -> "ToolResult":
        """Handle skill_begin tool call."""
        skill_name = args.get("skill_name", "")
        task = args.get("task", "")
        reason = args.get("reason", "")

        if not skill_name:
            return ToolResult(
                content=json.dumps({
                    "ok": False,
                    "error": "skill_name is required for skill_begin.",
                }),
                messages=messages,
                success=False,
            )

        # Resolve skill from registry (if available)
        skill_prompt = None
        skill_type = "normal"
        registry = self._engine._registry
        if registry:
            skill = registry.get(skill_name)
            if skill:
                skill_prompt = skill.build_prompt() if hasattr(skill, 'build_prompt') else None
                skill_type = skill.skill_type.value if hasattr(skill, 'skill_type') else "normal"
            elif skill_name == "meta":
                skill_type = "meta"
            else:
                # Unknown skill — still allow, but log
                logger.warning(
                    "skill_begin: '%s' not in registry, using as meta",
                    skill_name,
                )
                skill_type = "meta"
        elif skill_name == "meta":
            skill_type = "meta"

        try:
            # Handle auto_meta replacement (§4.6.7)
            stack = self._engine._stack
            config = self._engine._config

            if (config.auto_meta_explicit_mode == "replace_when_only_auto"
                    and stack.has_only_auto_meta()
                    and skill_name != "meta"):
                # Replace auto_meta with explicit skill
                auto_scope_id = stack.peek().scope_id
                end_result = self._engine._end_scope(
                    scope_id=auto_scope_id,
                    messages=messages,
                    report=f"Auto-meta replaced by explicit skill_begin({skill_name}).",
                )
                if end_result.success:
                    messages = end_result.messages

            # Begin the scope
            messages = self._engine._begin_scope(
                skill_name=skill_name,
                skill_type=skill_type,
                messages=messages,
                skill_prompt=skill_prompt,
            )

            top = self._engine._stack.peek()
            response = {
                "ok": True,
                "scope_id": top.scope_id,
                "skill_name": skill_name,
                "depth": top.depth,
                "task": task,
            }

            return ToolResult(
                content=json.dumps(response),
                messages=messages,
                success=True,
            )

        except RuntimeError as e:
            return ToolResult(
                content=json.dumps({
                    "ok": False,
                    "error": str(e),
                }),
                messages=messages,
                success=False,
            )

    def _handle_skill_end(
        self,
        args: Dict[str, Any],
        messages: List[Message],
    ) -> "ToolResult":
        """Handle skill_end tool call."""
        report = args.get("report", args.get("user_visible_summary", ""))
        scope_id = args.get("scope_id")

        try:
            result = self._engine._end_scope(
                scope_id=scope_id,
                messages=messages,
                report=report or None,
            )

            if result.success:
                response = {
                    "ok": True,
                    "scope_id": result.scope.id,
                    "skill_name": result.skill_name,
                    "summary": result.scope.summary[:500],
                    "tokens_saved": result.compact.tokens_saved,
                    "depth_after_pop": self._engine._stack.depth,
                }
                if result.scope.files_changed:
                    response["files_changed"] = result.scope.files_changed[:10]
                if result.scope.tools_used:
                    response["tools_used"] = dict(
                        list(result.scope.tools_used.items())[:8]
                    )

                return ToolResult(
                    content=json.dumps(response),
                    messages=result.messages,
                    success=True,
                )
            else:
                # Report rejected or other error
                return ToolResult(
                    content=json.dumps({
                        "ok": False,
                        "error": result.error,
                        "scope_id": result.scope.id if result.scope else None,
                    }),
                    messages=messages,
                    success=False,
                )

        except RuntimeError as e:
            return ToolResult(
                content=json.dumps({
                    "ok": False,
                    "error": str(e),
                }),
                messages=messages,
                success=False,
            )

    def _handle_recall(
        self,
        tool_name: str,
        args: Dict[str, Any],
        messages: List[Message],
    ) -> "ToolResult":
        """
        Handle memory_expand / memory_search tool calls.

        For memory_expand: the result is injected as a SYSTEM message
        into the message list, making it part of the ongoing context
        rather than a disposable tool response.

        The RecallSkill uses stateless tree-based ID navigation:
          - The "id" parameter encodes the full path (e.g. "abc123.files")
          - No hidden expansion state — the ID IS the state
        """
        recall = self._engine._recall
        if not recall:
            return ToolResult(
                content="Recall is not available. No memory store configured.",
                messages=messages,
                success=False,
            )

        try:
            result = recall.execute_tool(tool_name, args)

            # For memory_expand: always inject as context enrichment message
            if tool_name == "memory_expand":
                expand_id = args.get("id", "")

                enrichment_msg = Message(
                    role=MessageRole.SYSTEM,
                    content=result,
                    metadata={
                        "memory_expansion": True,
                        "expand_id": expand_id,
                    },
                )
                messages = messages + [enrichment_msg]

                return ToolResult(
                    content=f"Expanded '{expand_id or 'root'}'. "
                            f"Detail has been injected into context.",
                    messages=messages,
                    success=True,
                )

            return ToolResult(
                content=result,
                messages=messages,
                success=True,
            )
        except Exception as e:
            logger.error("Recall tool '%s' failed: %s", tool_name, e)
            return ToolResult(
                content=f"Recall tool error: {e}",
                messages=messages,
                success=False,
            )

    # ─────────────────────────────────────────
    # Tool Schemas
    # ─────────────────────────────────────────

    def _skill_begin_schema(self) -> Dict[str, Any]:
        return {
            "name": "skill_begin",
            "description": (
                "Open a new SUB-skill scope on top of the current stack.\n"
                "\n"
                "Each scope gives you an isolated working context: you can think, "
                "use tools, and gather state without polluting the parent scope. "
                "When you call skill_end, the entire detailed transcript of this "
                "scope is replaced by your one-line report — so a sub-skill is the "
                "primary mechanism for keeping long context windows tidy.\n"
                "\n"
                "WHEN TO USE:\n"
                "- Distinct sub-tasks that benefit from isolation: deep research, "
                "  long shell sessions, browsing flows, code-review, debugging, "
                "  multi-step planning.\n"
                "- Anything where the intermediate steps are noise once you have "
                "  the answer — they will be folded away by skill_end's report.\n"
                "\n"
                "WHEN NOT TO USE:\n"
                "- Do NOT open a 'meta' scope yourself. The system auto-opens one "
                "  as the bottom of the stack at every wake; you only ever close "
                "  it (see skill_end's CONTINUITY PROTOCOL).\n"
                "- Do NOT open a scope for a one-shot reply — overhead is not "
                "  worth it.\n"
                "\n"
                "STACK CONTRACT (LIFO):\n"
                "- Scopes are nested. You must close the innermost open scope "
                "  before any of its ancestors. Trying to close out of order is "
                "  a hard error.\n"
                "- The Active skill stack is shown to you at the bottom of every "
                "  context window — read it before deciding what to do."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": (
                            "Name of the skill to activate. Must be a registered "
                            "skill from the catalog. Do not pass 'meta' — that "
                            "is reserved for the auto-opened root scope."
                        ),
                    },
                    "task": {
                        "type": "string",
                        "description": (
                            "One-sentence description of what this scope will "
                            "accomplish. Read back to you in the scope's prompt; "
                            "also helps you stay focused."
                        ),
                    },
                    "reason": {
                        "type": "string",
                        "description": (
                            "Optional. Why this skill is needed right now "
                            "(audit/logging only — not shown to the user)."
                        ),
                    },
                },
                "required": ["skill_name"],
            },
        }

    def _skill_end_schema(self) -> Dict[str, Any]:
        return {
            "name": "skill_end",
            "description": (
                "Close the topmost open skill scope and write its permanent "
                "summary. There are TWO distinct patterns — pay attention to "
                "which one you are in.\n"
                "\n"
                "═══════════════════════════════════════════════════════════\n"
                "PATTERN A — closing a sub-skill you opened with skill_begin\n"
                "═══════════════════════════════════════════════════════════\n"
                "Pop a sub-scope you previously opened. Your report replaces "
                "every detailed message of that sub-task in the parent's view, "
                "so write what an outsider needs to know:\n"
                "  - What was accomplished (concrete outcomes, not effort).\n"
                "  - Files / resources touched.\n"
                "  - Key decisions and the rationale.\n"
                "  - Errors hit and how you resolved them.\n"
                "  - Anything left undone or worth following up.\n"
                "\n"
                "═══════════════════════════════════════════════════════════\n"
                "PATTERN B — closing the root 'meta' scope (CONTINUITY PROTOCOL)\n"
                "═══════════════════════════════════════════════════════════\n"
                "Before you call subagent_rest at the end of a turn, AND once "
                "the Active skill stack only has the root meta scope left, you "
                "MUST call:\n"
                "    skill_end(scope_id='<root meta scope_id>',\n"
                "              report='<1-3 sentence recap>')\n"
                "(The exact scope_id is shown to you in the Active skill stack "
                "block — copy it verbatim.)\n"
                "\n"
                "Why this matters — this is how you remember anything across\n"
                "wake/rest cycles:\n"
                "- Your report becomes summary.md for this turn's root scope.\n"
                "- On your NEXT wake, that summary appears as one entry in\n"
                "  <PREV_SCOPE_HISTORY> — alongside summaries from earlier\n"
                "  turns, oldest to newest. That block IS your long-term\n"
                "  conversational memory; nothing else carries it.\n"
                "- If you skip this call, the system falls back to using your\n"
                "  last chat_reply text as the summary. That is just your\n"
                "  closing words, not what the turn was about — future-you\n"
                "  will see a noisy, redundant timeline.\n"
                "\n"
                "How to write the Pattern B report:\n"
                "- 1-3 sentences. Tight. Information-dense.\n"
                "- Cover: (1) what the user wanted or what triggered the wake,\n"
                "  (2) what you did or decided, (3) any open thread the next\n"
                "  wake should pick up.\n"
                "- Write it for your future self, NOT for the user. Skip\n"
                "  pleasantries. No emoji.\n"
                "- Do NOT paste your chat_reply.message verbatim — that\n"
                "  carries zero new signal for the next wake.\n"
                "\n"
                "Examples (Pattern B):\n"
                "  GOOD:\n"
                "    \"User asked my name; introduced myself as 小牛 and asked\n"
                "     how they'd like to be called. Awaiting their preferred\n"
                "     form of address.\"\n"
                "  GOOD:\n"
                "    \"User reported missing PREV_SCOPE_HISTORY in context.\n"
                "     Diagnosed as PR-58 not deployed; ran deploy and backfilled\n"
                "     181 historical summaries. They will retest next session.\"\n"
                "  BAD (verbatim chat_reply, no signal):\n"
                "    \"大哥好！👋 有什么需要小弟帮忙的吗？您尽管吩咐！\"\n"
                "\n"
                "═══════════════════════════════════════════════════════════\n"
                "STACK CONTRACT (both patterns):\n"
                "- LIFO: only the topmost open scope can be closed. If a sub-\n"
                "  skill is still open, close it first; the root meta scope is\n"
                "  always the LAST close before rest.\n"
                "- The Active skill stack at the bottom of every context window\n"
                "  shows you the topmost scope_id and the close call to issue."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "report": {
                        "type": "string",
                        "description": (
                            "Permanent summary of this scope. Replaces all "
                            "detailed messages in the parent's view.\n"
                            "\n"
                            "Pattern A (sub-skill): be thorough — files "
                            "changed, decisions made, errors and resolutions, "
                            "follow-ups.\n"
                            "\n"
                            "Pattern B (root meta scope, continuity protocol): "
                            "1-3 sentences capturing user intent + your "
                            "action/decision + any open thread. This text "
                            "becomes one entry of <PREV_SCOPE_HISTORY> on "
                            "your next wake — write it for your future self, "
                            "not for the user. Do not paste chat_reply text "
                            "verbatim."
                        ),
                    },
                    "scope_id": {
                        "type": "string",
                        "description": (
                            "Scope ID to close. Must match the topmost open "
                            "scope (LIFO). For Pattern B, copy the root meta "
                            "scope_id verbatim from the Active skill stack "
                            "block. If omitted, the system closes the topmost "
                            "scope automatically — but passing it explicitly "
                            "is safer and avoids races."
                        ),
                    },
                },
                "required": ["report"],
            },
        }


# ─────────────────────────────────────────────
# ToolResult (returned by dispatch)
# ─────────────────────────────────────────────

class ToolResult:
    """Result of an engine tool dispatch."""

    __slots__ = ("content", "messages", "success")

    def __init__(
        self,
        content: str,
        messages: List[Message],
        success: bool = True,
    ):
        self.content = content
        self.messages = messages
        self.success = success
