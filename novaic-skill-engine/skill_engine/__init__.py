"""
Skill Engine — 渐进式技能加载引擎

完整功能:
- 三层渐进式披露（metadata → body → references）
- 多策略匹配（assigned / keyword / path 条件激活）
- 参数替换（$1, ${ARG_NAME}）
- 生命周期钩子（pre_invoke / post_invoke / on_error）
- Token 预算管理
- 全量兼容模式
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .arguments import parse_argument_names, substitute_arguments
from .hooks import (
    HookEvent,
    HooksConfig,
    execute_hook,
    register_hook_callback,
)
from .matcher import SkillMatcher
from .prompt import SkillPromptBuilder
from .protocols import SkillStore, TokenEstimator
from .registry import SkillRegistry
from .types import Skill, SkillBody, SkillMatchResult, SkillMetadata, SkillSource
from .fs_store import FileSystemSkillStore

logger = logging.getLogger("skill_engine")

__all__ = [
    # Facade
    "SkillEngine",
    # Core components
    "SkillRegistry",
    "SkillMatcher",
    "SkillPromptBuilder",
    # Types
    "Skill",
    "SkillMetadata",
    "SkillBody",
    "SkillMatchResult",
    "SkillSource",
    # Protocols
    "SkillStore",
    "TokenEstimator",
    # Arguments
    "substitute_arguments",
    "parse_argument_names",
    # Hooks
    "HookEvent",
    "HooksConfig",
    "execute_hook",
    "register_hook_callback",
    # File System Store
    "FileSystemSkillStore",
]


class SkillEngine:
    """
    技能引擎门面 — 一站式 API
    
    集成步骤：
    1. 实现 SkillStore protocol
    2. 创建 SkillEngine(store)
    3. engine.refresh()
    4. build_system_prompt_section() → 注入 system prompt
    5. load_and_format(skill_id, args) → Agent tool 回调
    """

    def __init__(
        self,
        store: SkillStore,
        estimator: Optional[TokenEstimator] = None,
        max_matches: int = 5,
        progressive: bool = True,
    ):
        self.registry = SkillRegistry(store, estimator)
        self.matcher = SkillMatcher(self.registry, max_matches)
        self.prompt_builder = SkillPromptBuilder(estimator)
        self._store = store
        self._progressive = progressive

    def refresh(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> int:
        return self.registry.refresh(user_id, agent_id)

    def build_system_prompt_section(
        self,
        task: Optional[str] = None,
        agent_id: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
    ) -> str:
        results = self.matcher.match_for_task(
            task=task or "",
            agent_id=agent_id,
            file_paths=file_paths,
        )

        if self._progressive:
            return self.prompt_builder.build_directory(results)
        else:
            skills = []
            for r in results:
                loaded = self.registry.load_skill_body(r.skill.id)
                if loaded:
                    skills.append(loaded)
            return self.prompt_builder.build_full_section(skills)

    def load_and_format(
        self,
        skill_id: str,
        args: str = "",
        named_args: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        按需加载技能 body 并返回格式化详情。
        支持参数替换。
        
        这是 Agent Tool 的核心回调。
        """
        skill = self.registry.load_skill_body(skill_id)
        if not skill:
            return f"❌ 技能 {skill_id} 不存在"

        # 执行 pre_invoke hook
        hooks = skill.metadata.extra.get("hooks") if hasattr(skill.metadata, 'extra') else None
        if hooks:
            hooks_config = HooksConfig.from_dict(hooks)
            execute_hook(hooks_config, HookEvent.PRE_INVOKE, {
                "skill_name": skill.name,
                "args": args,
            })

        detail = self.prompt_builder.build_skill_detail(skill)

        # 参数替换
        if args or named_args:
            arg_names = skill.body.arguments if skill.body else []
            detail = substitute_arguments(
                detail,
                args,
                named_args=named_args,
                arg_names=arg_names,
            )

        return detail

    def notify_file_operation(self, file_paths: List[str]) -> List[str]:
        results = self.matcher.match_for_task(
            task="",
            file_paths=file_paths,
            include_assigned=False,
        )
        return [r.skill.name for r in results if "path:" in r.reason]

    def reset_session(self) -> None:
        self.matcher.reset_activated()
        self.registry.clear_dynamic()

    def get_diagnostics(self) -> dict:
        return {
            "total_skills": self.registry.skill_count,
            "metadata_tokens": self.registry.total_metadata_tokens,
            "activated_conditional": self.matcher.activated_count,
            "progressive_mode": self._progressive,
        }
