"""
Context Stack — Meta Skill

The default scope wrapper. Used when no skill matches.
Ensures every user request is wrapped in a scope, even without a specific skill.

Lifecycle:
  checkpoint → (no prompt injection) → agent executes freely → summarize → reload
"""
from __future__ import annotations

from ..types import Skill, SkillType


class MetaSkill:
    """
    Factory for Meta Skills.
    
    Meta Skill = empty skill (no prompt/workflow) that provides a scope wrapper.
    The Agent works in "free mode" — no injected instructions.
    
    Why it matters:
      Without MetaSkill, messages from unmatched tasks float without scope coverage.
      With MetaSkill, every single message is under a scope → no orphan messages.
    """

    @staticmethod
    def create(name: str = "", task: str = "") -> Skill:
        """
        Create a Meta Skill for wrapping a task.
        
        The name defaults to the first 50 chars of the task.
        """
        if not name:
            name = task[:50].strip() if task else "ad-hoc task"

        return Skill(
            name=f"meta:{name}",
            skill_type=SkillType.META,
            prompt="",      # no prompt
            workflow="",    # no workflow
            description=f"Auto-scoped: {name}",
        )
