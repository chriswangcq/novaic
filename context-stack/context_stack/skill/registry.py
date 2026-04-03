"""
Context Stack — Skill Registry

Register, load, and retrieve skills.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .types import Skill, SkillType
from .matcher import SkillMatcher

logger = logging.getLogger("context_stack.skill.registry")


class SkillRegistry:
    """
    Central skill registry.
    
    Usage:
        registry = SkillRegistry()
        registry.register(my_skill)
        skill = registry.match(task="implement auth", agent_id="agent-1")
    """

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._matcher = SkillMatcher()

    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill
        logger.info("Registered skill: %s (%s)", skill.name, skill.skill_type.value)

    def register_many(self, skills: List[Skill]) -> None:
        for s in skills:
            self.register(s)

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def match(
        self,
        task: str,
        agent_id: str = "",
        file_paths: Optional[List[str]] = None,
    ) -> Optional[Skill]:
        """
        Match a task to the best skill.
        Returns None if no match (engine will use MetaSkill).
        """
        # Only match NORMAL skills — META and RECALL are triggered differently
        normal_skills = [
            s for s in self._skills.values()
            if s.skill_type == SkillType.NORMAL
        ]
        return self._matcher.match(normal_skills, task, agent_id, file_paths)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    @property
    def count(self) -> int:
        return len(self._skills)
