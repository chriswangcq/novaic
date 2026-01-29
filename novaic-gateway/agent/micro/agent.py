"""
MicroAgent - Lightweight agent for event filtering and conditional wake-up

Micro Agents are small, configurable agents that evaluate incoming events
to determine if they should wake up the main agent.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import re
import uuid


class EvalMode(Enum):
    """Evaluation mode for micro agents."""
    RULES = "rules"  # Rule-based evaluation only
    LLM = "llm"  # LLM-based evaluation only
    HYBRID = "hybrid"  # Rules first, then LLM if uncertain


@dataclass
class EvalResult:
    """Result of micro agent evaluation."""
    should_wake: bool
    confidence: float  # 0.0 to 1.0
    reason: str
    matched_rules: List[str] = field(default_factory=list)
    llm_response: Optional[str] = None
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "should_wake": self.should_wake,
            "confidence": self.confidence,
            "reason": self.reason,
            "matched_rules": self.matched_rules,
            "llm_response": self.llm_response,
            "duration_ms": self.duration_ms,
        }


@dataclass
class Rule:
    """A rule for micro agent evaluation."""
    id: str
    name: str
    pattern: str  # Regex pattern or keyword
    action: str = "wake"  # "wake", "ignore", "queue"
    priority: int = 0  # Higher = more important
    enabled: bool = True
    
    def matches(self, text: str) -> bool:
        """Check if text matches this rule."""
        if not self.enabled:
            return False
        try:
            return bool(re.search(self.pattern, text, re.IGNORECASE))
        except re.error:
            # Fallback to simple substring match
            return self.pattern.lower() in text.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "pattern": self.pattern,
            "action": self.action,
            "priority": self.priority,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data["name"],
            pattern=data["pattern"],
            action=data.get("action", "wake"),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
        )


@dataclass
class MicroAgent:
    """
    Micro Agent definition.
    
    A micro agent evaluates events and decides whether to wake the main agent.
    It can use rules, LLM evaluation, or a combination of both.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    
    # Evaluation mode
    mode: EvalMode = EvalMode.HYBRID
    
    # Rules for rule-based evaluation
    rules: List[Rule] = field(default_factory=list)
    
    # LLM prompt for LLM-based evaluation
    llm_prompt: str = """You are a filter agent. Decide if the following event should wake up the main AI agent.

Event:
{event}

Consider:
- Is this urgent or important?
- Does it require immediate attention?
- Can it wait or be ignored?

Respond with:
- WAKE if the main agent should be woken
- IGNORE if this can be ignored
- QUEUE if this can wait

Then explain briefly why."""
    
    # Configuration
    enabled: bool = True
    confidence_threshold: float = 0.7  # Minimum confidence to take action
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_rule(
        self,
        name: str,
        pattern: str,
        action: str = "wake",
        priority: int = 0,
    ) -> str:
        """
        Add a rule to this micro agent.
        
        Args:
            name: Rule name
            pattern: Regex pattern to match
            action: Action to take (wake, ignore, queue)
            priority: Rule priority
        
        Returns:
            Rule ID
        """
        rule = Rule(
            id=str(uuid.uuid4())[:8],
            name=name,
            pattern=pattern,
            action=action,
            priority=priority,
        )
        self.rules.append(rule)
        self.updated_at = datetime.now()
        return rule.id
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                del self.rules[i]
                self.updated_at = datetime.now()
                return True
        return False
    
    def evaluate_rules(self, event_text: str) -> EvalResult:
        """
        Evaluate event using rules only.
        
        Args:
            event_text: Text content of the event
        
        Returns:
            EvalResult with rule-based decision
        """
        matched = []
        
        # Sort rules by priority (higher first)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if rule.matches(event_text):
                matched.append(rule)
        
        if not matched:
            return EvalResult(
                should_wake=False,
                confidence=0.5,
                reason="No rules matched",
            )
        
        # Use highest priority matching rule
        top_rule = matched[0]
        
        return EvalResult(
            should_wake=top_rule.action == "wake",
            confidence=1.0,  # Rules are deterministic
            reason=f"Matched rule: {top_rule.name}",
            matched_rules=[r.name for r in matched],
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "mode": self.mode.value,
            "rules": [r.to_dict() for r in self.rules],
            "llm_prompt": self.llm_prompt,
            "enabled": self.enabled,
            "confidence_threshold": self.confidence_threshold,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MicroAgent":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            mode=EvalMode(data.get("mode", "hybrid")),
            rules=[Rule.from_dict(r) for r in data.get("rules", [])],
            llm_prompt=data.get("llm_prompt", cls.llm_prompt),
            enabled=data.get("enabled", True),
            confidence_threshold=data.get("confidence_threshold", 0.7),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )
