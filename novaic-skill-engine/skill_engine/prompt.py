"""
Skill Engine — Prompt Builder (提示词构建器)

核心：渐进式 prompt 构建
- build_directory(): 仅 Layer 1 元数据目录 → 注入 system prompt
- build_skill_detail(): Layer 2 body → tool 调用时返回
- build_full_section(): 传统全量注入（兼容模式）
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .protocols import DefaultTokenEstimator, TokenEstimator
from .types import Skill, SkillLoadState, SkillMatchResult

logger = logging.getLogger("skill_engine.prompt")


# ── 预算常量 ──

MAX_SKILLS_IN_PROMPT = 10         # 最多注入的技能数
MAX_DIRECTORY_TOKENS = 2000       # 技能目录的总 token 上限
MAX_SINGLE_SKILL_CHARS = 3000     # 单技能 body 字符上限（全量模式）
MAX_TOTAL_BODY_CHARS = 8000       # 全量模式总字符上限


class SkillPromptBuilder:
    """
    技能提示词构建器
    
    两种模式：
    1. 渐进式（推荐）：system prompt 注入目录，body 按需加载
    2. 全量式（兼容）：所有内容直接注入 system prompt
    
    Usage（渐进式）:
        builder = SkillPromptBuilder()
        
        # Step 1: 构建目录 → 注入 system prompt
        directory = builder.build_directory(matched_results)
        system_prompt += directory
        
        # Step 2: 用户/模型请求某个 skill 的详情
        detail = builder.build_skill_detail(skill)
    
    Usage（全量式，兼容现有架构）:
        section = builder.build_full_section(all_skills)
        system_prompt += section
    """

    def __init__(self, estimator: Optional[TokenEstimator] = None):
        self._estimator = estimator or DefaultTokenEstimator()

    # ── 渐进式模式（推荐）──

    def build_directory(
        self,
        results: List[SkillMatchResult],
        max_skills: int = MAX_SKILLS_IN_PROMPT,
        max_tokens: int = MAX_DIRECTORY_TOKENS,
    ) -> str:
        """
        构建 Layer 1 技能目录 — 仅元数据，用于注入 system prompt。
        
        输出格式:
            ## 可用技能
            以下技能可通过 load_skill_detail 工具加载详细指令：
            
            - **web-dev** (内置): 网页开发最佳实践 [当需要创建网页时使用]
            - **react** (自定义): React 组件开发指南
        
        Token 成本: ~100 tokens/skill，10 个技能 ≈ 1000 tokens
        """
        if not results:
            return ""

        results = results[:max_skills]
        lines = [
            "## 可用技能",
            "以下技能可通过 load_skill_detail 工具加载详细指令：",
            "",
        ]

        total_tokens = self._estimator.estimate("\n".join(lines))

        for r in results:
            meta = r.skill.metadata
            source_tag = f" ({meta.source.value})" if meta.source != "custom" else ""
            when = f" [适用: {meta.when_to_use}]" if meta.when_to_use else ""
            desc = meta.description[:120] if meta.description else ""

            line = f"- **{meta.name}**{source_tag}: {desc}{when}"
            line_tokens = self._estimator.estimate(line)

            if total_tokens + line_tokens > max_tokens:
                lines.append(f"_(更多技能因上下文预算限制已省略，共 {len(results)} 个)_")
                break

            lines.append(line)
            total_tokens += line_tokens

        return "\n".join(lines)

    def build_skill_detail(self, skill: Skill) -> str:
        """
        构建 Layer 2 技能详情 — 在 tool 调用时返回。
        
        调用方需确保 skill.body 已加载（通过 registry.load_skill_body）。
        """
        if skill.load_state == SkillLoadState.METADATA_ONLY:
            return (
                f"## 技能: {skill.name}\n\n"
                f"> {skill.metadata.description}\n\n"
                f"_(技能指令体尚未加载，请调用 load_skill_body 工具)_"
            )

        body = skill.body
        parts = [f"## 技能: {skill.name}"]

        if skill.metadata.description:
            parts.append(f"> {skill.metadata.description}")
        parts.append("")

        if body and body.prompt:
            parts.append(body.prompt)

        if body and body.workflow:
            parts.append(f"\n**工作流:**\n{body.workflow}")

        if body and body.allowed_tools:
            parts.append(f"\n**允许的工具:** {', '.join(body.allowed_tools)}")

        # Layer 3 引用文件清单
        if skill.references:
            parts.append("\n**引用文件:**")
            for ref in skill.references:
                parts.append(f"- `{ref.path}` (~{ref.token_estimate} tokens)")

        return "\n".join(parts)

    # ── 全量模式（兼容）──

    def build_full_section(
        self,
        skills: List[Skill],
        max_skills: int = MAX_SKILLS_IN_PROMPT,
        max_total_chars: int = MAX_TOTAL_BODY_CHARS,
        max_single_chars: int = MAX_SINGLE_SKILL_CHARS,
    ) -> str:
        """
        传统全量注入模式 — 兼容 NovAIC 现有 _build_skills_section。
        
        与现有实现的区别：
        1. 有硬上限（max_skills, max_total_chars, max_single_chars）
        2. 超长自动 compact（仅保留 name + description 摘要）
        3. 总量超限时截断并提示
        """
        if not skills:
            return ""

        skills = skills[:max_skills]
        parts = []
        total_chars = 0

        for skill in skills:
            text = self._format_skill_full(skill)

            # 单技能超长 → compact 模式
            if len(text) > max_single_chars:
                text = (
                    f"### {skill.name}\n"
                    f"> {skill.metadata.description[:200]}\n\n"
                    f"_(技能内容超长 {len(text)} 字符，已省略全文。"
                    f"可通过 load_skill_detail 工具获取完整内容)_"
                )

            # 总量超限 → 截断
            if total_chars + len(text) > max_total_chars:
                parts.append(
                    f"_(更多技能因上下文预算限制已省略，"
                    f"已加载 {len(parts)}/{len(skills)} 个)_"
                )
                break

            parts.append(text)
            total_chars += len(text)

        header = "\n\n## 已加载的技能 (Domain Knowledge)\n\n"
        return header + "\n\n---\n\n".join(parts)

    def _format_skill_full(self, skill: Skill) -> str:
        """格式化单个技能的完整内容"""
        meta = skill.metadata
        parts = [f"### {meta.name}"]

        if meta.source.value == "builtin":
            parts[0] += " (内置)"

        if meta.description:
            parts.append(f"> {meta.description}")

        if skill.body:
            if skill.body.prompt:
                parts.append(f"\n{skill.body.prompt}")
            if skill.body.workflow:
                parts.append(f"\n**工作流:**\n{skill.body.workflow}")

        return "\n".join(parts)
