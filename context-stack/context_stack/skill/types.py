"""
Context Stack — Skill Types
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class SkillType(Enum):
    NORMAL = "normal"       # domain skill with prompt + workflow
    META = "meta"           # default scope wrapper, no prompt
    RECALL = "recall"       # memory exploration skill


@dataclass
class Skill:
    """
    A skill definition. Can be loaded from YAML or created programmatically.
    
    For NORMAL skills: name, prompt, workflow, keywords, etc.
    For META: just a name (prompt is empty)
    For RECALL: has special pre/post hooks (memory tools)
    """
    name: str
    skill_type: SkillType = SkillType.NORMAL
    
    # Matching
    keywords: List[str] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=list)  # glob patterns
    assigned_agents: List[str] = field(default_factory=list)
    priority: int = 100     # lower = higher priority
    
    # Content
    prompt: str = ""        # system prompt to inject
    workflow: str = ""      # step-by-step workflow
    constraints: str = ""   # rules / guardrails
    
    # Tool control
    allowed_tools: Optional[List[str]] = None   # None = all tools allowed
    
    # Hooks (skill-specific, in addition to global hooks)
    pre_hooks: List[Callable] = field(default_factory=list)
    post_hooks: List[Callable] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def build_prompt(self) -> str:
        """Build the full prompt to inject into system message."""
        if not self.prompt and not self.workflow:
            return ""
        
        parts = []
        if self.prompt:
            parts.append(f"## Skill: {self.name}\n\n{self.prompt}")
        if self.workflow:
            parts.append(f"### Workflow\n\n{self.workflow}")
        if self.constraints:
            parts.append(f"### Constraints\n\n{self.constraints}")
        return "\n\n".join(parts)
