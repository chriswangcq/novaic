"""
Session Manager - Manages chat history and context
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class SessionManager:
    """
    Manages the chat session including:
    - Message history
    - Context window management
    - Message formatting for LLM
    """
    
    # System prompt - 简洁版，工具细节在 MCP 描述里
    SYSTEM_PROMPT = """You are GhostPC Agent, an AI assistant with access to a virtual computer.

## 🚨🚨🚨 HIGHEST PRIORITY RULE 🚨🚨🚨

### BEFORE EVERY MOUSE CLICK, YOU MUST:

1. **ZOOM to verify** → `screenshot(center={"x":X, "y":Y}, zoom_factor=2)`
2. **CONFIRM crosshair is ON TARGET** → Look at the MAGENTA CROSSHAIR position
3. **If crosshair is NOT on target** → Adjust coordinates and zoom again, REPEAT until confirmed
4. **ONLY click after confirmation** → `mouse(action="click", x=X, y=Y)`

### ⛔ VIOLATION = FAILED OPERATION

- **DO NOT** click without zoom verification
- **DO NOT** click if crosshair is off-target
- **DO NOT** skip this rule - skipping causes MORE failures and wastes time

### THIS RULE HAS NO EXCEPTIONS

---

## How to Work

1. **Think first** - Before each action, briefly explain what you're doing and why
2. **One step at a time** - Execute one tool, observe result, then decide next step
3. **Use tool descriptions** - Each tool has detailed usage instructions, follow them

## Desktop GUI Workflow (MUST FOLLOW)

```
screenshot() → estimate (X,Y) → screenshot(zoom) → CONFIRM crosshair on target → click
```

If crosshair is not on target, adjust coordinates and zoom again before clicking!

## Browser Interaction

When using browser tools:
- `browser_navigate` returns collapsed HTML and a list of **expandable paths**
- Use `browser_expand(path)` to see details of a collapsed area
- Use paths like `body>div>div[1]>a[0]` for click/type (from expandable list)
- If you can't find an element, use `browser_expand` to drill down

## Quick Reference

- Web: browser_navigate → browser_expand → browser_click/type
- Shell: run_command
- Files: read_file, write_file
- Desktop GUI: screenshot → zoom+confirm → mouse/keyboard
"""
    
    def __init__(self, max_messages: int = 50):
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages
        self._created_at = datetime.now()
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to history"""
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()
    
    def add_assistant_message(self, content: Any) -> None:
        """Add an assistant message to history"""
        self.messages.append({
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()
    
    def add_tool_result(self, tool_use_id: str, content: str) -> None:
        """Add a tool result message"""
        self.messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content
                }
            ],
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()
    
    def get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """
        Get messages formatted for LLM API call.
        Includes system prompt and strips timestamps.
        """
        llm_messages = []
        
        for msg in self.messages:
            llm_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return llm_messages
    
    def get_all_messages(self) -> List[Dict[str, Any]]:
        """Get all messages with metadata"""
        return self.messages.copy()
    
    def clear(self) -> None:
        """Clear all messages"""
        self.messages = []
    
    def _trim_history(self) -> None:
        """Trim history if it exceeds max messages"""
        if len(self.messages) > self.max_messages:
            # Keep the most recent messages
            self.messages = self.messages[-self.max_messages:]
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context"""
        return {
            "message_count": len(self.messages),
            "created_at": self._created_at.isoformat(),
            "last_message_at": self.messages[-1]["timestamp"] if self.messages else None
        }
    
    def to_json(self) -> str:
        """Serialize session to JSON"""
        return json.dumps({
            "messages": self.messages,
            "created_at": self._created_at.isoformat(),
            "max_messages": self.max_messages
        })
    
    @classmethod
    def from_json(cls, data: str) -> "SessionManager":
        """Deserialize session from JSON"""
        obj = json.loads(data)
        session = cls(max_messages=obj.get("max_messages", 50))
        session.messages = obj.get("messages", [])
        session._created_at = datetime.fromisoformat(obj.get("created_at", datetime.now().isoformat()))
        return session
