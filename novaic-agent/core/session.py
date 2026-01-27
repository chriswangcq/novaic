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

## 🚨 MOUSE CONTROL: AIM → EXECUTE (Two-Phase)

### ALL mouse clicks MUST use aim_id. NO direct coordinates allowed!

**WORKFLOW:**
```
screenshot() → estimate target at (X, Y)
     ↓
mouse(action='aim', x=X, y=Y) → get aim_id + zoomed screenshot
     ↓
YOU JUDGE (look at the MAGENTA CROSSHAIR):
  - Crosshair ON target → mouse(action='click', aim_id='...')
  - Crosshair CLOSE but off → re-aim with adjusted coordinates
  - Crosshair FAR from target → re-aim with zoom=2
```

### ⛔ FORBIDDEN:
- mouse(action='click', x=500, y=300)  ← WRONG! No direct x/y!
- Clicking without aim_id

### ✅ CORRECT:
```python
# Step 1: Aim
mouse(action='aim', x=500, y=300)  # Returns aim_id='aim_abc123'

# Step 2: Execute (if crosshair on target)
mouse(action='click', aim_id='aim_abc123')
```

---

## How to Work

1. **Think first** - Before each action, briefly explain what you're doing and why
2. **One step at a time** - Execute one tool, observe result, then decide next step
3. **You judge** - Look at the crosshair position and decide: execute or re-aim

## Browser Interaction

When using browser tools:
- `browser_navigate` returns collapsed HTML and a list of **expandable paths**
- Use `browser_expand(path)` to see details of a collapsed area
- Use paths like `body>div>div[1]>a[0]` for click/type (from expandable list)

## Quick Reference

- Desktop GUI: screenshot → aim → (you judge crosshair) → execute
- Web: browser_navigate → browser_expand → browser_click/type
- Shell: run_command
- Files: read_file, write_file
"""
    
    def __init__(self, max_messages: int = 50):
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages
        self._created_at = datetime.now()
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to history. Skips empty content."""
        # Skip empty content to avoid API errors
        if not content:
            return
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()
    
    def add_assistant_message(self, content: Any) -> None:
        """Add an assistant message to history. Skips empty content."""
        # Skip empty content to avoid API errors
        if not content and content != 0:
            return
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
        Filters out messages with empty content (except final assistant message).
        """
        llm_messages = []
        
        for msg in self.messages:
            content = msg["content"]
            # Skip messages with empty content (API requirement)
            if not content and content != 0:  # Allow 0 but not empty string/None
                continue
            llm_messages.append({
                "role": msg["role"],
                "content": content
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
