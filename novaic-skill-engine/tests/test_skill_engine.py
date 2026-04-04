"""
Skill Engine — Comprehensive Tests

Coverage:
  - SkillRegistry: registration, dedup, progressive loading
  - SkillMatcher: keyword, path, assigned matching
  - SkillPromptBuilder: directory, detail, full section output
  - Arguments: positional, named, cleanup
  - Hooks: config parsing, callback execution
  - FileSystemSkillStore: SKILL.md scanning, frontmatter parsing, override
"""

from __future__ import annotations

import os
import tempfile
import textwrap
from pathlib import Path
from typing import Dict, List, Optional

import pytest

# ─────────────────────────────────────────
# Imports
# ─────────────────────────────────────────

from skill_engine.types import (
    Skill,
    SkillBody,
    SkillMatchResult,
    SkillMetadata,
    SkillReference,
    SkillSource,
    SkillLoadState,
)
from skill_engine.registry import SkillRegistry
from skill_engine.matcher import SkillMatcher
from skill_engine.prompt import SkillPromptBuilder
from skill_engine.arguments import substitute_arguments, parse_argument_names
from skill_engine.hooks import (
    HookEvent,
    HooksConfig,
    execute_hook,
    register_hook_callback,
    unregister_hook_callback,
    clear_callbacks,
)
from skill_engine.fs_store import FileSystemSkillStore


# ─────────────────────────────────────────
# Test fixtures
# ─────────────────────────────────────────

class InMemorySkillStore:
    """Minimal SkillStore implementation for testing."""

    def __init__(self, skills: Optional[List[Skill]] = None):
        self._skills: Dict[str, Skill] = {}
        self._agent_skills: Dict[str, List[str]] = {}
        if skills:
            for s in skills:
                self._skills[s.id] = s

    def add(self, skill: Skill) -> None:
        self._skills[skill.id] = skill

    def bind_agent(self, agent_id: str, skill_ids: List[str]) -> None:
        self._agent_skills[agent_id] = skill_ids

    def list_metadata(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> List[SkillMetadata]:
        return [s.metadata for s in self._skills.values()]

    def load_body(self, skill_id: str) -> Optional[SkillBody]:
        skill = self._skills.get(skill_id)
        if skill and skill.body:
            return skill.body
        return None

    def load_references(self, skill_id: str) -> List[SkillReference]:
        skill = self._skills.get(skill_id)
        if skill:
            return skill.references
        return []

    def get_agent_skills(self, agent_id: str) -> List[str]:
        return self._agent_skills.get(agent_id, [])


def _make_skill(
    name: str,
    skill_id: Optional[str] = None,
    description: str = "",
    keywords: Optional[List[str]] = None,
    paths: Optional[List[str]] = None,
    priority: int = 0,
    source: SkillSource = SkillSource.CUSTOM,
    body_prompt: str = "",
    workflow: str = "",
) -> Skill:
    sid = skill_id or f"test-{name}"
    meta = SkillMetadata(
        id=sid,
        name=name,
        description=description,
        source=source,
        keywords=keywords or [],
        paths=paths or [],
        priority=priority,
    )
    body = SkillBody(prompt=body_prompt, workflow=workflow) if body_prompt else None
    return Skill(metadata=meta, body=body)


# ─── Registry Tests ──────────────────────

class TestRegistry:
    def test_refresh_loads_all(self):
        s1 = _make_skill("web-dev", description="Web development")
        s2 = _make_skill("debug", description="Debugging")
        store = InMemorySkillStore([s1, s2])

        reg = SkillRegistry(store)
        count = reg.refresh()

        assert count == 2
        assert reg.skill_count == 2

    def test_get_by_name(self):
        s = _make_skill("react", description="React components")
        store = InMemorySkillStore([s])
        reg = SkillRegistry(store)
        reg.refresh()

        result = reg.get_by_name("react")
        assert result is not None
        assert result.name == "react"

    def test_get_by_id(self):
        s = _make_skill("test", skill_id="unique-1")
        store = InMemorySkillStore([s])
        reg = SkillRegistry(store)
        reg.refresh()

        assert reg.get_by_id("unique-1") is not None
        assert reg.get_by_id("nope") is None

    def test_priority_dedup(self):
        """Higher-priority skill wins when IDs collide."""
        s_low = _make_skill("v1", skill_id="same-id", priority=1)
        s_high = _make_skill("v2", skill_id="same-id", priority=5)
        store = InMemorySkillStore([s_low])
        reg = SkillRegistry(store)
        reg.refresh()

        # Register higher priority manually
        reg._register(Skill(metadata=s_high.metadata))
        assert reg.get_by_id("same-id").name == "v2"

    def test_progressive_load_body(self):
        s = _make_skill(
            "coding",
            body_prompt="Write clean code",
            workflow="1. Read 2. Write 3. Test",
        )
        store = InMemorySkillStore([s])
        reg = SkillRegistry(store)
        reg.refresh()

        skill = reg.get_by_name("coding")
        assert skill.load_state == SkillLoadState.METADATA_ONLY

        loaded = reg.load_skill_body(skill.id)
        assert loaded is not None
        assert loaded.load_state == SkillLoadState.BODY_LOADED
        assert loaded.body.prompt == "Write clean code"

    def test_load_nonexistent_body(self):
        store = InMemorySkillStore()
        reg = SkillRegistry(store)
        reg.refresh()

        assert reg.load_skill_body("nope") is None

    def test_dynamic_registration(self):
        store = InMemorySkillStore()
        reg = SkillRegistry(store)
        reg.refresh()
        assert reg.skill_count == 0

        s = _make_skill("dynamic-1")
        reg.register_dynamic(s)
        assert reg.skill_count == 1
        assert reg.get_by_name("dynamic-1") is not None

        reg.clear_dynamic()
        assert reg.skill_count == 0

    def test_assigned_skills(self):
        s1 = _make_skill("skill-a", skill_id="a")
        s2 = _make_skill("skill-b", skill_id="b")
        store = InMemorySkillStore([s1, s2])
        store.bind_agent("agent-1", ["a"])

        reg = SkillRegistry(store)
        reg.refresh()

        assigned = reg.get_assigned_skills("agent-1")
        assert len(assigned) == 1
        assert assigned[0].name == "skill-a"


# ─── Matcher Tests ───────────────────────

class TestMatcher:
    def test_keyword_match(self):
        s = _make_skill("python", keywords=["python", "django"])
        store = InMemorySkillStore([s])
        reg = SkillRegistry(store)
        reg.refresh()
        matcher = SkillMatcher(reg)

        results = matcher.match_for_task("I need a python script")
        assert len(results) == 1
        assert "keyword:python" in results[0].reason

    def test_keyword_no_match(self):
        s = _make_skill("python", keywords=["python"])
        store = InMemorySkillStore([s])
        reg = SkillRegistry(store)
        reg.refresh()
        matcher = SkillMatcher(reg)

        results = matcher.match_for_task("I need a rust program")
        assert len(results) == 0

    def test_path_match(self):
        s = _make_skill("react", paths=["src/**/*.tsx", "src/**/*.jsx"])
        store = InMemorySkillStore([s])
        reg = SkillRegistry(store)
        reg.refresh()
        matcher = SkillMatcher(reg)

        results = matcher.match_for_task(
            "",
            file_paths=["src/components/Button.tsx"],
        )
        assert len(results) == 1
        assert "path:" in results[0].reason

    def test_path_no_match(self):
        s = _make_skill("react", paths=["src/**/*.tsx"])
        store = InMemorySkillStore([s])
        reg = SkillRegistry(store)
        reg.refresh()
        matcher = SkillMatcher(reg)

        results = matcher.match_for_task("", file_paths=["lib/utils.py"])
        assert len(results) == 0

    def test_assigned_highest_priority(self):
        s1 = _make_skill("assigned-one", skill_id="a1")
        s2 = _make_skill("keyword-one", keywords=["hello"])
        store = InMemorySkillStore([s1, s2])
        store.bind_agent("agent", ["a1"])
        reg = SkillRegistry(store)
        reg.refresh()
        matcher = SkillMatcher(reg)

        results = matcher.match_for_task("hello", agent_id="agent")
        assert len(results) == 2
        assert results[0].reason == "assigned"  # highest score

    def test_max_matches_limit(self):
        skills = [_make_skill(f"s{i}", keywords=[f"kw{i}"]) for i in range(10)]
        store = InMemorySkillStore(skills)
        reg = SkillRegistry(store)
        reg.refresh()
        matcher = SkillMatcher(reg, max_matches=3)

        task = " ".join(f"kw{i}" for i in range(10))
        results = matcher.match_for_task(task)
        assert len(results) <= 3

    def test_conditional_activation_dedup(self):
        """Path-activated skill should not re-activate on second call."""
        s = _make_skill("auto-react", paths=["*.tsx"])
        store = InMemorySkillStore([s])
        reg = SkillRegistry(store)
        reg.refresh()
        matcher = SkillMatcher(reg)

        r1 = matcher.match_for_task("", file_paths=["App.tsx"])
        r2 = matcher.match_for_task("", file_paths=["Page.tsx"])
        assert len(r1) == 1
        assert len(r2) == 0  # already activated

        matcher.reset_activated()
        r3 = matcher.match_for_task("", file_paths=["App.tsx"])
        assert len(r3) == 1  # re-activated after reset


# ─── Prompt Builder Tests ────────────────

class TestPromptBuilder:
    def test_build_directory(self):
        s = _make_skill("web-dev", description="Web development best practices")
        result = SkillMatchResult(skill=s, reason="keyword:web", score=5.0)
        builder = SkillPromptBuilder()

        text = builder.build_directory([result])
        assert "web-dev" in text
        assert "可用技能" in text

    def test_build_empty_directory(self):
        builder = SkillPromptBuilder()
        assert builder.build_directory([]) == ""

    def test_build_skill_detail_with_body(self):
        s = _make_skill(
            "coding",
            description="Write clean code",
            body_prompt="Always use type hints.",
            workflow="1. Read\n2. Write",
        )
        builder = SkillPromptBuilder()

        text = builder.build_skill_detail(s)
        assert "coding" in text
        assert "Always use type hints" in text
        assert "工作流" in text

    def test_build_skill_detail_metadata_only(self):
        s = _make_skill("test", description="Testing")
        builder = SkillPromptBuilder()

        text = builder.build_skill_detail(s)
        assert "尚未加载" in text

    def test_build_full_section(self):
        skills = [
            _make_skill("s1", body_prompt="Do thing 1"),
            _make_skill("s2", body_prompt="Do thing 2"),
        ]
        builder = SkillPromptBuilder()

        text = builder.build_full_section(skills)
        assert "已加载的技能" in text
        assert "s1" in text
        assert "s2" in text

    def test_full_section_truncation(self):
        """Very long skills are compacted."""
        s = _make_skill("long", body_prompt="x" * 5000)
        builder = SkillPromptBuilder()

        text = builder.build_full_section([s], max_single_chars=100)
        assert "超长" in text or "已省略" in text

    def test_directory_token_budget(self):
        skills = [
            _make_skill(f"skill-{i}", description="A" * 200)
            for i in range(20)
        ]
        results = [
            SkillMatchResult(skill=s, reason="test", score=1.0)
            for s in skills
        ]
        builder = SkillPromptBuilder()

        text = builder.build_directory(results, max_tokens=500)
        assert "已省略" in text or len(text) < 3000


# ─── Arguments Tests ─────────────────────

class TestArguments:
    def test_positional_args(self):
        result = substitute_arguments("Deploy to $1", "production")
        assert result == "Deploy to production"

    def test_multiple_positional(self):
        result = substitute_arguments("$1 + $2 = awesome", "foo bar")
        assert result == "foo + bar = awesome"

    def test_named_args(self):
        result = substitute_arguments(
            "Deploy ${APP} to ${ENV}",
            "",
            named_args={"APP": "myapp", "ENV": "prod"},
        )
        assert result == "Deploy myapp to prod"

    def test_arguments_placeholder(self):
        result = substitute_arguments("Run: $ARGUMENTS", "test --verbose")
        assert result == "Run: test --verbose"

    def test_arg_names_mapping(self):
        result = substitute_arguments(
            "File: ${FILE_PATH}",
            "src/main.py",
            arg_names=["FILE_PATH"],
        )
        assert result == "File: src/main.py"

    def test_unmatched_cleanup(self):
        result = substitute_arguments("${MISSING} remains", "")
        assert result == " remains"

    def test_parse_argument_names_list(self):
        assert parse_argument_names(["arg1", "arg2"]) == ["arg1", "arg2"]

    def test_parse_argument_names_string(self):
        assert parse_argument_names("arg1, arg2") == ["arg1", "arg2"]

    def test_parse_argument_names_none(self):
        assert parse_argument_names(None) == []


# ─── Hooks Tests ─────────────────────────

class TestHooks:
    def setup_method(self):
        clear_callbacks()

    def test_parse_hooks_config_empty(self):
        config = HooksConfig.from_dict(None)
        assert not config.has_hook(HookEvent.PRE_INVOKE)

    def test_parse_hooks_config_string(self):
        config = HooksConfig.from_dict({
            "pre_invoke": "echo hello",
        })
        assert config.has_hook(HookEvent.PRE_INVOKE)
        hook = config.get_hook(HookEvent.PRE_INVOKE)
        assert hook.command == "echo hello"

    def test_parse_hooks_config_dict(self):
        config = HooksConfig.from_dict({
            "on_error": {
                "callback_id": "handler_v1",
                "timeout": 60,
            },
        })
        hook = config.get_hook(HookEvent.ON_ERROR)
        assert hook.callback_id == "handler_v1"
        assert hook.timeout == 60

    def test_execute_callback(self):
        results = []
        register_hook_callback("test_cb", lambda **kw: results.append(kw))

        config = HooksConfig.from_dict({
            "pre_invoke": {"callback_id": "test_cb"},
        })
        execute_hook(config, HookEvent.PRE_INVOKE, {"skill_name": "test"})

        assert len(results) == 1
        assert results[0]["skill_name"] == "test"

    def test_execute_shell_hook(self):
        config = HooksConfig.from_dict({
            "post_invoke": "notify-send done",
        })
        result = execute_hook(config, HookEvent.POST_INVOKE)
        assert result is not None
        assert "__HOOK_SHELL__" in result

    def test_callback_error_resilience(self):
        def bad_callback(**kw):
            raise ValueError("boom")

        register_hook_callback("bad", bad_callback)
        config = HooksConfig.from_dict({
            "on_error": {"callback_id": "bad"},
        })
        # Should not raise
        result = execute_hook(config, HookEvent.ON_ERROR)
        assert result is None

    def test_unknown_event_ignored(self):
        config = HooksConfig.from_dict({
            "unknown_event": "echo test",
        })
        assert not config.has_hook(HookEvent.PRE_INVOKE)


# ─── FileSystem SkillStore Tests ─────────

class TestFileSystemSkillStore:
    def _create_skill_dir(self, tmpdir: str, name: str, frontmatter: str, body: str = "") -> str:
        """Create a SKILL.md in a subdirectory."""
        skill_dir = os.path.join(tmpdir, name)
        os.makedirs(skill_dir, exist_ok=True)
        content = f"---\n{frontmatter}\n---\n{body}"
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write(content)
        return skill_dir

    def test_scan_single_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_skill_dir(
                tmpdir, "web-dev",
                'name: web-dev\ndescription: Web development best practices',
                'Always use semantic HTML.',
            )
            store = FileSystemSkillStore(roots=[tmpdir])
            metadata_list = store.list_metadata()

            assert len(metadata_list) == 1
            assert metadata_list[0].name == "web-dev"
            assert metadata_list[0].description == "Web development best practices"

    def test_scan_multiple_skills(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_skill_dir(tmpdir, "skill-a", "name: skill-a\ndescription: A")
            self._create_skill_dir(tmpdir, "skill-b", "name: skill-b\ndescription: B")
            store = FileSystemSkillStore(roots=[tmpdir])
            meta = store.list_metadata()
            assert len(meta) == 2

    def test_load_body(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_skill_dir(
                tmpdir, "coding",
                "name: coding\ndescription: Code review",
                "Always review for:\n1. Type safety\n2. Error handling",
            )
            store = FileSystemSkillStore(roots=[tmpdir])
            meta = store.list_metadata()
            body = store.load_body(meta[0].id)

            assert body is not None
            assert "Type safety" in body.prompt

    def test_load_body_with_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            body_text = textwrap.dedent("""\
                Be thorough in code review.

                ## Workflow
                1. Read the code
                2. Check for bugs
                3. Write feedback
            """)
            self._create_skill_dir(
                tmpdir, "review",
                "name: review\ndescription: Code review",
                body_text,
            )
            store = FileSystemSkillStore(roots=[tmpdir])
            meta = store.list_metadata()
            body = store.load_body(meta[0].id)

            assert body.workflow != ""
            assert "Read the code" in body.workflow

    def test_keywords_and_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_skill_dir(
                tmpdir, "react",
                'name: react\ndescription: React\nkeywords: [react, jsx, tsx]\npaths: ["src/**/*.tsx"]',
            )
            store = FileSystemSkillStore(roots=[tmpdir])
            meta = store.list_metadata()

            assert "react" in meta[0].keywords
            assert "src/**/*.tsx" in meta[0].paths

    def test_multi_root_override(self):
        """Later root overrides earlier root for same-name skills."""
        with tempfile.TemporaryDirectory() as root1, \
             tempfile.TemporaryDirectory() as root2:
            self._create_skill_dir(root1, "shared", "name: shared\ndescription: From root1")
            self._create_skill_dir(root2, "shared", "name: shared\ndescription: From root2")

            store = FileSystemSkillStore(roots=[root1, root2])
            meta = store.list_metadata()

            assert len(meta) == 1
            assert meta[0].description == "From root2"

    def test_no_frontmatter_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = os.path.join(tmpdir, "bad")
            os.makedirs(skill_dir)
            with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
                f.write("Just some text without frontmatter")

            store = FileSystemSkillStore(roots=[tmpdir])
            meta = store.list_metadata()
            assert len(meta) == 0

    def test_load_references(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = self._create_skill_dir(
                tmpdir, "with-refs",
                "name: with-refs\ndescription: Has references",
                "Main prompt",
            )
            # Add reference files
            with open(os.path.join(skill_dir, "examples.py"), "w") as f:
                f.write("def example(): pass")

            store = FileSystemSkillStore(roots=[tmpdir])
            meta = store.list_metadata()
            refs = store.load_references(meta[0].id)

            assert len(refs) == 1
            assert "examples.py" in refs[0].path

    def test_empty_roots(self):
        store = FileSystemSkillStore(roots=["/nonexistent/path"])
        meta = store.list_metadata()
        assert len(meta) == 0

    def test_add_root(self):
        store = FileSystemSkillStore(roots=[])
        assert len(store.roots) == 0
        store.add_root("/tmp/my_skills")
        assert len(store.roots) == 1

    def test_priority_parsing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_skill_dir(
                tmpdir, "high-pri",
                "name: high-pri\ndescription: Important\npriority: 10",
            )
            store = FileSystemSkillStore(roots=[tmpdir])
            meta = store.list_metadata()
            assert meta[0].priority == 10

    def test_source_detection(self):
        """Skills in .agents/ directories get CUSTOM source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = os.path.join(tmpdir, ".agents", "skills")
            os.makedirs(agents_dir)
            skill_dir = os.path.join(agents_dir, "custom-skill")
            os.makedirs(skill_dir)
            with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
                f.write("---\nname: custom-skill\ndescription: Custom\n---\nBody")

            store = FileSystemSkillStore(roots=[agents_dir])
            meta = store.list_metadata()
            assert meta[0].source == SkillSource.CUSTOM


# ─── SkillEngine Facade Tests ────────────

class TestSkillEngineFacade:
    def test_full_workflow(self):
        from skill_engine import SkillEngine

        s1 = _make_skill("web", keywords=["web", "html"], body_prompt="Use semantic HTML")
        s2 = _make_skill("python", keywords=["python"], body_prompt="Use type hints")
        store = InMemorySkillStore([s1, s2])

        engine = SkillEngine(store, progressive=True)
        engine.refresh()

        # Build system prompt section
        section = engine.build_system_prompt_section(task="Build a web page")
        assert "web" in section

        # Load and format skill detail
        detail = engine.load_and_format("test-web")
        assert "semantic HTML" in detail

    def test_non_progressive_mode(self):
        from skill_engine import SkillEngine

        s = _make_skill("test", keywords=["build"], body_prompt="Test body content")
        store = InMemorySkillStore([s])

        engine = SkillEngine(store, progressive=False)
        engine.refresh()

        section = engine.build_system_prompt_section(task="build something")
        assert "已加载的技能" in section
        assert "test" in section.lower()

    def test_notify_file_operation(self):
        from skill_engine import SkillEngine

        s = _make_skill("react", paths=["*.tsx"])
        store = InMemorySkillStore([s])

        engine = SkillEngine(store)
        engine.refresh()

        activated = engine.notify_file_operation(["App.tsx"])
        assert "react" in activated

    def test_diagnostics(self):
        from skill_engine import SkillEngine

        store = InMemorySkillStore([_make_skill("x"), _make_skill("y")])
        engine = SkillEngine(store)
        engine.refresh()

        diag = engine.get_diagnostics()
        assert diag["total_skills"] == 2
        assert diag["progressive_mode"] is True

    def test_session_reset(self):
        from skill_engine import SkillEngine

        s = _make_skill("auto", paths=["*.tsx"])
        store = InMemorySkillStore([s])
        engine = SkillEngine(store)
        engine.refresh()

        engine.notify_file_operation(["App.tsx"])
        assert engine.get_diagnostics()["activated_conditional"] == 1

        engine.reset_session()
        assert engine.get_diagnostics()["activated_conditional"] == 0
