"""
Skill Engine — Matcher (技能匹配器)

支持多种匹配策略：
1. 手动绑定（assigned）
2. 关键词匹配（keyword）
3. 文件路径匹配（path — 条件激活）
4. 预留 embedding 匹配接口
"""

from __future__ import annotations

import fnmatch
import logging
import re
from typing import List, Optional, Set

from .registry import SkillRegistry
from .types import Skill, SkillMatchResult, SkillSource

logger = logging.getLogger("skill_engine.matcher")


class SkillMatcher:
    """
    技能匹配器
    
    Usage:
        matcher = SkillMatcher(registry)
        
        # 基于任务文本匹配
        results = matcher.match_for_task(
            task="帮我写一个 React 组件",
            agent_id="agent-123",
        )
        
        # 基于文件路径匹配（条件激活）
        activated = matcher.activate_for_paths(
            file_paths=["src/components/Button.tsx"],
        )
    """

    def __init__(
        self,
        registry: SkillRegistry,
        max_matches: int = 5,
    ):
        self._registry = registry
        self._max_matches = max_matches
        self._activated: Set[str] = set()  # 已激活的条件技能 ID

    def match_for_task(
        self,
        task: str,
        agent_id: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        include_assigned: bool = True,
    ) -> List[SkillMatchResult]:
        """
        综合匹配：合并 assigned + keyword + path 匹配结果。
        返回按优先级排序的 SkillMatchResult 列表。
        
        Args:
            task: 用户任务描述
            agent_id: Agent ID（用于获取绑定技能）
            file_paths: 涉及的文件路径（用于条件激活）
            include_assigned: 是否包含 agent 绑定的技能
        """
        results: List[SkillMatchResult] = []
        seen_ids: Set[str] = set()

        # 1. Agent 绑定的技能（最高优先级）
        if include_assigned and agent_id:
            for skill in self._registry.get_assigned_skills(agent_id):
                if skill.id not in seen_ids:
                    results.append(SkillMatchResult(
                        skill=skill,
                        reason="assigned",
                        score=10.0,
                    ))
                    seen_ids.add(skill.id)

        # 2. 关键词匹配
        if task:
            keyword_matches = self._match_by_keywords(task)
            for match in keyword_matches:
                if match.skill.id not in seen_ids:
                    results.append(match)
                    seen_ids.add(match.skill.id)

        # 3. 文件路径匹配（条件激活）
        if file_paths:
            path_matches = self._match_by_paths(file_paths)
            for match in path_matches:
                if match.skill.id not in seen_ids:
                    results.append(match)
                    seen_ids.add(match.skill.id)

        # 排序：score 降序
        results.sort(key=lambda r: r.score, reverse=True)

        # 截断到 max_matches
        if len(results) > self._max_matches:
            results = results[:self._max_matches]

        logger.info(
            "[SkillMatcher] task=%s | matched=%d | reasons=%s",
            (task or "")[:60],
            len(results),
            [f"{r.skill.name}({r.reason})" for r in results],
        )

        return results

    # ── 关键词匹配 ──

    def _match_by_keywords(self, task: str) -> List[SkillMatchResult]:
        """基于 skill.keywords 的子串匹配"""
        task_lower = task.lower()
        results = []

        for skill in self._registry.all_skills():
            if not skill.metadata.keywords:
                continue
            for kw in skill.metadata.keywords:
                if kw.lower() in task_lower:
                    results.append(SkillMatchResult(
                        skill=skill,
                        reason=f"keyword:{kw}",
                        score=5.0 + skill.metadata.priority,
                    ))
                    break  # 一个 skill 只匹配一次

        return results

    # ── 文件路径匹配（条件激活）──

    def _match_by_paths(self, file_paths: List[str]) -> List[SkillMatchResult]:
        """
        基于 skill.paths 的 glob 匹配（gitignore 风格）。
        
        借鉴 Claude Code 的 activateConditionalSkillsForPaths：
        只要文件路径匹配任一 pattern，就激活该技能。
        """
        results = []

        for skill in self._registry.all_skills():
            if not skill.metadata.paths:
                continue
            if skill.id in self._activated:
                continue  # 已激活

            if self._paths_match(skill.metadata.paths, file_paths):
                self._activated.add(skill.id)
                results.append(SkillMatchResult(
                    skill=skill,
                    reason=f"path:{skill.metadata.paths[0]}",
                    score=3.0 + skill.metadata.priority,
                ))
                logger.info(
                    "[SkillMatcher] Activated conditional skill: %s",
                    skill.name,
                )

        return results

    @staticmethod
    def _paths_match(patterns: List[str], file_paths: List[str]) -> bool:
        """检查任一 file_path 是否匹配任一 pattern"""
        for fp in file_paths:
            for pattern in patterns:
                if fnmatch.fnmatch(fp, pattern):
                    return True
        return False

    # ── 状态管理 ──

    def reset_activated(self) -> None:
        """清除条件激活状态（新会话时调用）"""
        self._activated.clear()

    @property
    def activated_count(self) -> int:
        return len(self._activated)
