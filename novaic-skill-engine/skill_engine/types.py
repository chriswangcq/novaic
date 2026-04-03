"""
Skill Engine — Core Types

所有数据结构都是 frozen dataclass，不依赖任何外部框架。
集成方只需将自己的数据映射到这些类型即可。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SkillSource(str, Enum):
    """技能来源"""
    BUILTIN = "builtin"          # 系统内置（文件系统 / 编译进代码）
    CUSTOM = "custom"            # 用户自定义（DB / Entangled 创建）
    MATCHED = "matched"          # 运行时自动匹配（keyword / embedding）
    DYNAMIC = "dynamic"          # 运行时文件操作触发发现
    MCP = "mcp"                  # MCP Server 远程提供


class SkillLoadState(str, Enum):
    """渐进式加载状态"""
    METADATA_ONLY = "metadata"   # 仅元数据（Layer 1）
    BODY_LOADED = "body"         # 指令体已加载（Layer 2）
    FULLY_LOADED = "full"        # 所有引用文件已加载（Layer 3）


@dataclass(frozen=True)
class SkillMetadata:
    """
    Layer 1: 技能元数据 — 始终注入 system prompt
    
    设计原则：这是唯一进入初始 system prompt 的内容。
    Token 成本 ~50-150 tokens/skill，可安全支撑 100+ 技能。
    """
    id: str
    name: str
    description: str = ""
    when_to_use: str = ""           # 告诉模型何时调用此技能
    source: SkillSource = SkillSource.CUSTOM
    keywords: List[str] = field(default_factory=list)
    paths: List[str] = field(default_factory=list)  # 条件激活路径（glob）
    version: str = ""
    priority: int = 0               # 越大越优先


@dataclass(frozen=True)
class SkillBody:
    """
    Layer 2: 技能指令体 — 仅在调用时加载
    
    包含完整的 prompt 指令、工作流步骤等。
    """
    prompt: str = ""
    workflow: str = ""
    allowed_tools: List[str] = field(default_factory=list)
    arguments: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillReference:
    """
    Layer 3: 引用文件 — 仅在 body 引用时按需加载
    """
    path: str
    content: str
    token_estimate: int = 0


@dataclass
class Skill:
    """
    完整技能实体 — 三层渐进式结构
    
    metadata 始终存在，body 和 references 按需加载。
    
    Usage:
        skill = Skill(metadata=SkillMetadata(id="1", name="web-dev"))
        assert skill.load_state == SkillLoadState.METADATA_ONLY
        
        skill.body = SkillBody(prompt="当用户需要创建网页时...")
        assert skill.load_state == SkillLoadState.BODY_LOADED
    """
    metadata: SkillMetadata
    body: Optional[SkillBody] = None
    references: List[SkillReference] = field(default_factory=list)

    @property
    def load_state(self) -> SkillLoadState:
        if self.references:
            return SkillLoadState.FULLY_LOADED
        if self.body:
            return SkillLoadState.BODY_LOADED
        return SkillLoadState.METADATA_ONLY

    @property
    def id(self) -> str:
        return self.metadata.id

    @property
    def name(self) -> str:
        return self.metadata.name


@dataclass(frozen=True)
class SkillMatchResult:
    """技能匹配结果，包含匹配原因（可观测性）"""
    skill: Skill
    reason: str               # "assigned", "keyword:python", "path:src/**.tsx"
    score: float = 1.0        # 匹配分数，用于排序
