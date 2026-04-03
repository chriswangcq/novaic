"""
Tests for skill/ — types, registry, matcher.
"""
import pytest

from context_stack.skill.types import Skill, SkillType
from context_stack.skill.registry import SkillRegistry
from context_stack.skill.matcher import SkillMatcher
from context_stack.skill.builtins.meta import MetaSkill


class TestSkill:
    def test_build_prompt_with_both(self):
        s = Skill(
            name="test",
            prompt="You are an expert.",
            workflow="Step 1. Do this.\nStep 2. Do that.",
        )
        prompt = s.build_prompt()
        assert "You are an expert" in prompt
        assert "Step 1" in prompt
        assert "test" in prompt

    def test_build_prompt_empty(self):
        s = Skill(name="meta-skill")
        assert s.build_prompt() == ""

    def test_build_prompt_with_constraints(self):
        s = Skill(
            name="test",
            prompt="Do stuff.",
            constraints="Never delete files.",
        )
        prompt = s.build_prompt()
        assert "Never delete files" in prompt

    def test_skill_defaults(self):
        s = Skill(name="test")
        assert s.skill_type == SkillType.NORMAL
        assert s.keywords == []
        assert s.allowed_tools is None
        assert s.priority == 100

    def test_skill_types(self):
        for t in SkillType:
            s = Skill(name="x", skill_type=t)
            assert s.skill_type == t


class TestMetaSkill:
    def test_creates_meta_skill(self):
        skill = MetaSkill.create(task="Fix the bug in file.py")
        assert skill.skill_type == SkillType.META
        assert "meta:" in skill.name
        assert skill.prompt == ""
        assert skill.workflow == ""

    def test_name_from_task(self):
        skill = MetaSkill.create(task="Refactor the database module")
        assert "Refactor" in skill.name

    def test_name_truncated(self):
        long_task = "A" * 200
        skill = MetaSkill.create(task=long_task)
        assert len(skill.name) < 100  # "meta:" + 50 chars

    def test_default_name_when_empty(self):
        skill = MetaSkill.create()
        assert "meta:" in skill.name
        assert len(skill.name) > 5

    def test_explicit_name_overrides(self):
        skill = MetaSkill.create(name="my-scope", task="some task")
        assert "my-scope" in skill.name


class TestSkillMatcher:
    def setup_method(self):
        self.matcher = SkillMatcher()
        self.skills = [
            Skill(name="auth", keywords=["auth", "login", "password"], priority=100),
            Skill(name="db", keywords=["database", "sql", "postgres"], priority=100),
            Skill(name="ui", keywords=["frontend", "react", "component"], priority=200),
            Skill(name="agent-1-skill", assigned_agents=["agent-1"], priority=50),
        ]

    def test_keyword_match(self):
        result = self.matcher.match(self.skills, "implement user authentication")
        assert result is not None
        assert result.name == "auth"

    def test_multi_keyword_match_higher_score(self):
        result = self.matcher.match(self.skills, "database sql query")
        assert result is not None
        assert result.name == "db"

    def test_no_match_returns_none(self):
        result = self.matcher.match(self.skills, "something completely unrelated xyz")
        assert result is None

    def test_assigned_agent_wins(self):
        result = self.matcher.match(
            self.skills,
            "implement auth login",  # would match 'auth' on keywords
            agent_id="agent-1",
        )
        # assigned agent (100pts) beats keyword match (10-20pts)
        assert result.name == "agent-1-skill"

    def test_file_pattern_match(self):
        skills = [
            Skill(name="python-skill", file_patterns=["*.py", "src/**/*.py"]),
            Skill(name="ts-skill", file_patterns=["*.ts", "*.tsx"]),
        ]
        result = self.matcher.match(
            skills, "modify this file",
            file_paths=["src/app.py"]
        )
        assert result.name == "python-skill"

    def test_priority_tiebreaker(self):
        skills = [
            Skill(name="low-priority", keywords=["auth"], priority=200),
            Skill(name="high-priority", keywords=["auth"], priority=50),
        ]
        result = self.matcher.match(skills, "auth task")
        assert result.name == "high-priority"

    def test_case_insensitive_keywords(self):
        skills = [Skill(name="auth", keywords=["AUTH", "Login"])]
        result = self.matcher.match(skills, "implement auth module")
        assert result is not None


class TestSkillRegistry:
    def setup_method(self):
        self.registry = SkillRegistry()

    def test_register_and_get(self):
        s = Skill(name="my-skill")
        self.registry.register(s)
        assert self.registry.get("my-skill") is s

    def test_get_missing_returns_none(self):
        assert self.registry.get("nonexistent") is None

    def test_register_many(self):
        skills = [Skill(name=f"skill-{i}") for i in range(5)]
        self.registry.register_many(skills)
        assert self.registry.count == 5

    def test_match_normal_skills_only(self):
        # META and RECALL skills should not be matched
        self.registry.register(Skill(name="normal", keywords=["test"], skill_type=SkillType.NORMAL))
        self.registry.register(Skill(name="meta", keywords=["test"], skill_type=SkillType.META))
        self.registry.register(Skill(name="recall", keywords=["test"], skill_type=SkillType.RECALL))
        result = self.registry.match("test task")
        assert result is not None
        assert result.name == "normal"

    def test_list_skills(self):
        self.registry.register(Skill(name="a"))
        self.registry.register(Skill(name="b"))
        skills = self.registry.list_skills()
        names = [s.name for s in skills]
        assert "a" in names
        assert "b" in names

    def test_overwrite_on_same_name(self):
        self.registry.register(Skill(name="dupe", prompt="v1"))
        self.registry.register(Skill(name="dupe", prompt="v2"))
        assert self.registry.count == 1
        assert self.registry.get("dupe").prompt == "v2"
