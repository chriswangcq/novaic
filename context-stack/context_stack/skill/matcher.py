"""
Context Stack — Skill Matcher

Multi-strategy matching: keywords, file patterns, assigned agents.
"""
from __future__ import annotations

import fnmatch
import logging
import re
from typing import List, Optional

from .types import Skill

logger = logging.getLogger("context_stack.skill.matcher")


class SkillMatcher:
    """
    Matches a task/context to the best skill.
    
    Strategies (checked in order):
    1. assigned_agents — direct agent assignment
    2. file_patterns — glob match on mentioned file paths
    3. keywords — keyword match on task text
    """

    def match(
        self,
        skills: List[Skill],
        task: str,
        agent_id: str = "",
        file_paths: Optional[List[str]] = None,
    ) -> Optional[Skill]:
        """
        Find the best matching skill.
        Returns None if no match (caller should use MetaSkill).
        """
        candidates: List[tuple] = []  # (score, priority, skill)
        
        for skill in skills:
            score = self._score(skill, task, agent_id, file_paths or [])
            if score > 0:
                candidates.append((score, skill.priority, skill))
        
        if not candidates:
            return None
        
        # Sort by score desc, then priority asc (lower = higher)
        candidates.sort(key=lambda x: (-x[0], x[1]))
        best = candidates[0][2]
        
        logger.info(
            "Matched skill '%s' (score=%d) for task: %s",
            best.name, candidates[0][0], task[:80],
        )
        return best

    def _score(
        self,
        skill: Skill,
        task: str,
        agent_id: str,
        file_paths: List[str],
    ) -> int:
        score = 0
        
        # Strategy 1: assigned agent (highest priority)
        if agent_id and agent_id in skill.assigned_agents:
            score += 100
        
        # Strategy 2: file pattern matching
        if file_paths and skill.file_patterns:
            for fp in file_paths:
                for pattern in skill.file_patterns:
                    if fnmatch.fnmatch(fp, pattern):
                        score += 50
                        break
        
        # Strategy 3: keyword matching
        if skill.keywords:
            task_lower = task.lower()
            for kw in skill.keywords:
                if kw.lower() in task_lower:
                    score += 10
        
        return score
