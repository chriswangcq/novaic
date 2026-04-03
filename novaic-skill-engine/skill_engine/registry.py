"""
Skill Engine — Registry (技能注册表)

管理技能的注册、去重、优先级排序。
支持多源技能合并（builtin + custom + dynamic）。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from .protocols import DefaultTokenEstimator, SkillStore, TokenEstimator
from .types import Skill, SkillBody, SkillLoadState, SkillMetadata, SkillSource

logger = logging.getLogger("skill_engine.registry")


class SkillRegistry:
    """
    技能注册表 — 统一管理所有来源的技能
    
    核心职责：
    1. 从 SkillStore 加载元数据
    2. 按需加载 body（渐进式披露）
    3. 去重（相同 ID 只保留高优先级）
    4. 提供按 ID/名称快速查找
    
    Usage:
        store = MySkillStore(...)
        registry = SkillRegistry(store)
        registry.refresh()
        
        # Layer 1: 获取所有元数据（用于 system prompt）
        all_skills = registry.all_skills()
        
        # Layer 2: 按需加载某个 skill 的 body
        skill = registry.load_skill_body("skill-123")
    """

    def __init__(
        self,
        store: SkillStore,
        estimator: Optional[TokenEstimator] = None,
    ):
        self._store = store
        self._estimator = estimator or DefaultTokenEstimator()

        # 核心存储
        self._skills: Dict[str, Skill] = {}          # id → Skill
        self._by_name: Dict[str, Skill] = {}          # name → Skill
        self._dynamic: Dict[str, Skill] = {}           # 动态发现的技能

        # 统计
        self._total_metadata_tokens = 0

    # ── 初始化 & 刷新 ──

    def refresh(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> int:
        """
        从 store 重新加载所有技能元数据。
        返回加载的技能数量。
        """
        metadata_list = self._store.list_metadata(user_id, agent_id)

        self._skills.clear()
        self._by_name.clear()
        self._total_metadata_tokens = 0

        for meta in metadata_list:
            skill = Skill(metadata=meta)
            self._register(skill)

        # 合并动态发现的技能
        for skill in self._dynamic.values():
            if skill.id not in self._skills:
                self._register(skill)

        logger.info(
            "[SkillRegistry] Refreshed: %d skills, ~%d metadata tokens",
            len(self._skills),
            self._total_metadata_tokens,
        )
        return len(self._skills)

    def _register(self, skill: Skill) -> None:
        """注册单个技能，处理去重和优先级"""
        existing = self._skills.get(skill.id)
        if existing and existing.metadata.priority >= skill.metadata.priority:
            logger.debug(
                "[SkillRegistry] Skipping %s (lower priority than existing)",
                skill.name,
            )
            return

        self._skills[skill.id] = skill
        self._by_name[skill.name] = skill
        self._total_metadata_tokens += self._estimate_metadata_tokens(skill)

    def _estimate_metadata_tokens(self, skill: Skill) -> int:
        """仅计算 Layer 1 元数据的 token 成本"""
        text = " ".join(
            filter(None, [
                skill.metadata.name,
                skill.metadata.description,
                skill.metadata.when_to_use,
            ])
        )
        return self._estimator.estimate(text)

    # ── 查询 ──

    def all_skills(self) -> List[Skill]:
        """返回所有已注册技能（仅包含 metadata）"""
        return list(self._skills.values())

    def get_by_id(self, skill_id: str) -> Optional[Skill]:
        return self._skills.get(skill_id)

    def get_by_name(self, name: str) -> Optional[Skill]:
        return self._by_name.get(name)

    def get_assigned_skills(self, agent_id: str) -> List[Skill]:
        """获取 agent 绑定的技能"""
        ids = self._store.get_agent_skills(agent_id)
        return [self._skills[sid] for sid in ids if sid in self._skills]

    @property
    def total_metadata_tokens(self) -> int:
        """所有技能 Layer 1 的总 token 成本"""
        return self._total_metadata_tokens

    @property
    def skill_count(self) -> int:
        return len(self._skills)

    # ── 渐进式加载 ──

    def load_skill_body(self, skill_id: str) -> Optional[Skill]:
        """
        按需加载技能的 Layer 2（body）。
        返回加载后的 Skill，或 None（不存在）。
        
        这是渐进式披露的核心方法。
        集成到 runtime 时，可注册为一个 tool。
        """
        skill = self._skills.get(skill_id)
        if not skill:
            logger.warning("[SkillRegistry] Skill %s not found", skill_id)
            return None

        if skill.load_state != SkillLoadState.METADATA_ONLY:
            return skill  # 已加载

        body = self._store.load_body(skill_id)
        if body:
            skill.body = body
            logger.info(
                "[SkillRegistry] Loaded body for %s (%s), ~%d chars",
                skill.name,
                skill_id,
                len(body.prompt) + len(body.workflow),
            )

        return skill

    def load_skill_references(self, skill_id: str) -> Optional[Skill]:
        """按需加载技能的 Layer 3（引用文件）"""
        skill = self.load_skill_body(skill_id)  # 确保 body 已加载
        if not skill:
            return None

        if skill.load_state == SkillLoadState.FULLY_LOADED:
            return skill

        refs = self._store.load_references(skill_id)
        skill.references = refs
        return skill

    # ── 动态技能 ──

    def register_dynamic(self, skill: Skill) -> None:
        """注册运行时动态发现的技能"""
        self._dynamic[skill.id] = skill
        if skill.id not in self._skills:
            self._register(skill)
            logger.info(
                "[SkillRegistry] Dynamic skill registered: %s", skill.name,
            )

    def clear_dynamic(self) -> None:
        """清除所有动态技能（会话结束时调用）"""
        for sid in list(self._dynamic.keys()):
            self._skills.pop(sid, None)
            skill = self._dynamic.get(sid)
            if skill:
                self._by_name.pop(skill.name, None)
        self._dynamic.clear()
