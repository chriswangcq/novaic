"""
Context Stack — Unified Engine End-to-End Demo

Demonstrates the complete lifecycle for all 3 skill types:
  1. Normal Skill  → skill-driven task with prompt injection
  2. Meta Skill    → unmatched task auto-scoped
  3. Recall Skill  → memory exploration with tools
"""

import sys
sys.path.insert(0, ".")

from context_stack import (
    ContextEngine,
    CompactConfig,
    Message,
    MessageRole,
    Skill,
    SkillType,
)


# ─────────────────────────────────────────────
# Mock implementations (host provides real ones)
# ─────────────────────────────────────────────

class MockSummarizer:
    def summarize(self, messages, max_tokens=2000, instructions=""):
        tools = [m.tool_name for m in messages if m.tool_name]
        return (
            f"Completed the task. {len(tools)} tool calls made. "
            f"Decision: chose bcrypt for password hashing. "
            f"Created user model and API endpoint. All tests pass."
        )


class MockCounter:
    def count(self, text):
        return max(1, len(text) // 4)
    def count_messages(self, messages):
        return sum(self.count(m.content) for m in messages)


class MockExecutor:
    """
    Simulates an agent loop.
    
    For normal/meta: adds tool calls and assistant responses.
    For recall: uses memory_expand/memory_search tools.
    """
    def __init__(self, engine=None):
        self._engine = engine

    def execute(self, messages, extra_tools=None):
        # Check if recall tools are available
        has_recall = extra_tools and any(t["name"] == "memory_expand" for t in extra_tools)
        
        if has_recall and self._engine:
            return self._execute_recall(messages)
        else:
            return self._execute_normal(messages)
    
    def _execute_normal(self, messages):
        """Simulate normal agent work."""
        new = list(messages)
        new.append(Message(role=MessageRole.ASSISTANT, content="Let me check the project structure."))
        new.append(Message(role=MessageRole.TOOL, content="src/\n  app.py\n  models/\n  routes/", tool_name="read_file"))
        new.append(Message(role=MessageRole.ASSISTANT, content="I'll use bcrypt for hashing. Creating the user model..."))
        new.append(Message(role=MessageRole.TOOL, content="Created file src/models/user.py", tool_name="write_file"))
        new.append(Message(role=MessageRole.TOOL, content="Created file src/routes/auth.py with POST /api/v1/users", tool_name="write_file"))
        new.append(Message(role=MessageRole.TOOL, content="FAILED: test_duplicate_email - IntegrityError", tool_name="run_command"))
        new.append(Message(role=MessageRole.ASSISTANT, content="Need to add email uniqueness validation. Fixing..."))
        new.append(Message(role=MessageRole.TOOL, content="Modified src/routes/auth.py — added email check", tool_name="write_file"))
        new.append(Message(role=MessageRole.TOOL, content="All 5 tests passed ✓", tool_name="run_command"))
        new.append(Message(role=MessageRole.ASSISTANT, content="Done! User registration implemented with bcrypt and email validation."))
        return new

    def _execute_recall(self, messages):
        """Simulate recall: agent uses memory_expand and memory_search tools."""
        new = list(messages)
        
        # Agent decides to search first
        new.append(Message(role=MessageRole.ASSISTANT, content="Let me search for relevant past work."))
        
        # Agent calls memory_search
        search_result = self._engine.handle_recall_tool("memory_search", {"query": "password bcrypt"})
        new.append(Message(
            role=MessageRole.TOOL,
            content=search_result,
            tool_name="memory_search",
            tool_input='{"query": "password bcrypt"}',
        ))
        
        # Agent calls memory_expand on the matched scope
        new.append(Message(role=MessageRole.ASSISTANT, content="Found relevant scope. Let me expand it for details."))
        
        # Get scope list first
        expand_result = self._engine.handle_recall_tool("memory_expand", {"level": 0})
        new.append(Message(
            role=MessageRole.TOOL,
            content=expand_result,
            tool_name="memory_expand",
            tool_input='{"level": 0}',
        ))
        
        # Agent answers based on what it found
        new.append(Message(
            role=MessageRole.ASSISTANT,
            content="Based on the past work: we used bcrypt for password hashing. "
                    "The decision was made for dependency simplicity over argon2. "
                    "The implementation is in src/models/user.py and src/routes/auth.py."
        ))
        return new


# ─────────────────────────────────────────────
# Build initial conversation
# ─────────────────────────────────────────────

def initial_messages():
    return [
        Message(role=MessageRole.SYSTEM, content="You are a coding assistant."),
        Message(role=MessageRole.USER, content="Implement user registration with password hashing."),
    ]


# ─────────────────────────────────────────────
# Main demo
# ─────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  Context Stack — Unified Engine Demo")
    print("  Skill Execution = Context Management = Memory Management")
    print("=" * 70)

    # Initialize
    executor = MockExecutor()
    engine = ContextEngine(
        executor=executor,
        summarizer=MockSummarizer(),
        counter=MockCounter(),
        config=CompactConfig(context_window=200_000),
    )
    # Give executor a reference to engine for recall tool dispatch
    executor._engine = engine

    # Register a domain skill
    auth_skill = Skill(
        name="user-auth",
        skill_type=SkillType.NORMAL,
        keywords=["auth", "login", "register", "password"],
        prompt="You are an authentication specialist. Use bcrypt for hashing.",
        workflow="1. Create user model\n2. Create auth routes\n3. Run tests",
        description="User authentication implementation",
    )
    engine.registry.register(auth_skill)

    messages = initial_messages()

    # ════════════════════════════════════════════
    # TEST 1: Normal Skill (matched)
    # ════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("1️⃣  NORMAL SKILL: engine.match_and_run()")
    print("─" * 70)

    result = engine.match_and_run(
        messages=messages,
        task="Implement user registration with password hashing",
    )

    print(f"   ✅ Skill matched:  {result.skill_name}")
    print(f"   Messages:         {len(messages)} → {len(result.messages)}")
    print(f"   Tokens saved:     {result.compact.tokens_saved}")
    print(f"   Scope ID:         {result.scope.id}")
    print(f"   Files changed:    {result.scope.files_changed}")
    print(f"   Tools used:       {result.scope.tools_used}")
    print(f"   Errors:           {result.scope.errors}")
    print(f"\n   📝 Summary (first 200 chars):")
    print(f"   {result.compact.summary[:200]}")

    messages = result.messages

    # ════════════════════════════════════════════
    # TEST 2: Meta Skill (no matching skill)
    # ════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("2️⃣  META SKILL: engine.run_meta() — no matching skill")
    print("─" * 70)

    messages.append(Message(
        role=MessageRole.USER,
        content="Refactor the database connection to use connection pooling",
    ))

    result = engine.run_meta(
        messages=messages,
        task="Refactor the database connection to use connection pooling",
    )

    print(f"   ✅ Skill:          {result.skill_name}")
    print(f"   Messages:         → {len(result.messages)}")
    print(f"   Tokens saved:     {result.compact.tokens_saved}")
    print(f"   Scope ID:         {result.scope.id}")

    messages = result.messages

    # ════════════════════════════════════════════
    # TEST 3: Recall Skill (memory exploration)
    # ════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("3️⃣  RECALL SKILL: engine.run_recall() — memory exploration")
    print("─" * 70)

    messages.append(Message(
        role=MessageRole.USER,
        content="What password hashing did we use before?",
    ))

    result = engine.run_recall(
        messages=messages,
        query="password hashing bcrypt",
    )

    print(f"   ✅ Skill:          {result.skill_name}")
    print(f"   Messages:         → {len(result.messages)}")
    print(f"   Tokens saved:     {result.compact.tokens_saved}")
    print(f"   Scope ID:         {result.scope.id}")
    print(f"   Tools used:       {result.scope.tools_used}")
    print(f"   (memory_search and memory_expand were used by the agent)")

    messages = result.messages

    # ════════════════════════════════════════════
    # TEST 4: Recall tools standalone
    # ════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("4️⃣  RECALL TOOLS: Direct tool execution")
    print("─" * 70)

    # memory_expand level 0
    print("\n   📋 memory_expand(level=0):")
    result_l0 = engine.handle_recall_tool("memory_expand", {"level": 0})
    for line in result_l0.split("\n")[:8]:
        print(f"   {line}")
    print("   ...")

    # memory_search
    print("\n   🔍 memory_search('bcrypt'):")
    result_search = engine.handle_recall_tool("memory_search", {"query": "bcrypt"})
    for line in result_search.split("\n")[:6]:
        print(f"   {line}")
    print("   ...")

    # ════════════════════════════════════════════
    # TEST 5: Status
    # ════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("5️⃣  STATUS: engine.status()")
    print("─" * 70)

    status = engine.status(messages)
    print(f"   Used tokens:      {status.used_tokens}")
    print(f"   Budget:           {status.budget_tokens}")
    print(f"   Usage:            {status.usage_ratio:.1%}")
    print(f"   Total scopes:     {status.total_scopes}")
    print(f"   Compacted:        {status.compacted_scopes}")
    print(f"   Recall available: {status.recall_available}")
    print(f"   Tokens saved:     {status.total_tokens_saved}")
    print(f"   Lifecycles run:   {status.total_compactions}")

    # ════════════════════════════════════════════
    # TEST 6: List scopes
    # ════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("6️⃣  LIST SCOPES: engine.list_scopes()")
    print("─" * 70)

    for s in engine.list_scopes():
        print(f"   [{s['id']}] {s['name']}")
        print(f"     Skill: {s['skill']}, Tools: {s['tools']}, Duration: {s['duration']}")
        print(f"     Tokens saved: {s['tokens_saved']}, Raw stored: {s['has_raw']}")

    # ════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  ✅ All tests passed!")
    print(f"  Total lifecycles: {engine.status().total_compactions}")
    print(f"  Total tokens saved: {engine.status().total_tokens_saved}")
    print("=" * 70)


if __name__ == "__main__":
    main()
