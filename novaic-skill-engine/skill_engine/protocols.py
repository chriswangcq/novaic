"""
Skill Engine — Protocols (接口协议)

定义集成方需要实现的接口。使用 Protocol 而非 ABC，
集成方不需要继承，只需实现对应方法即可（鸭子类型）。
"""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol, runtime_checkable

from .types import Skill, SkillBody, SkillMetadata, SkillReference


@runtime_checkable
class SkillStore(Protocol):
    """
    技能存储协议 — 集成方实现此接口以提供技能数据
    
    NovAIC 集成示例:
        class NovAICSkillStore:
            def __init__(self, skill_repo: SkillRepository):
                self._repo = skill_repo
            
            def list_metadata(self, user_id, agent_id):
                skills = self._repo.list_all(user_id)
                return [SkillMetadata(id=s["id"], name=s["name"], ...) for s in skills]
            
            def load_body(self, skill_id):
                s = self._repo.get_by_id(skill_id)
                return SkillBody(prompt=s["prompt"], workflow=s["workflow"])
    """

    def list_metadata(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> List[SkillMetadata]:
        """列出所有可用技能的元数据（Layer 1）"""
        ...

    def load_body(self, skill_id: str) -> Optional[SkillBody]:
        """按需加载单个技能的指令体（Layer 2）"""
        ...

    def load_references(self, skill_id: str) -> List[SkillReference]:
        """按需加载单个技能的引用文件（Layer 3），可选实现"""
        ...

    def get_agent_skills(self, agent_id: str) -> List[str]:
        """获取 agent 绑定的技能 ID 列表"""
        ...


@runtime_checkable
class TokenEstimator(Protocol):
    """
    Token 估算协议
    
    集成方可提供精确的 tokenizer 实现，
    引擎提供默认的粗估实现（字符数 / 4）。
    """

    def estimate(self, text: str) -> int:
        """估算文本的 token 数"""
        ...


@runtime_checkable
class SkillBodyLoader(Protocol):
    """
    技能 Body 异步加载协议
    
    用于渐进式加载场景下，从 tool 回调中触发加载。
    集成方可以实现异步版本以支持网络/DB 调用。
    """

    def load(self, skill_id: str) -> Optional[SkillBody]:
        """同步加载技能 Body"""
        ...


class DefaultTokenEstimator:
    """默认 token 估算器：字符数 / 4（粗估）"""

    def estimate(self, text: str) -> int:
        return max(1, len(text) // 4)
