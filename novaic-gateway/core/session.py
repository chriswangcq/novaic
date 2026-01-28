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
    
    # System prompt - 遵循 MCP 最佳实践
    # 工具详细描述在 MCP Tool descriptions 中
    # Skills (领域知识) 在 Agent 层动态注入
    SYSTEM_PROMPT = """You are NovAIC Agent, an AI assistant with access to a virtual computer through MCP (Model Context Protocol).

## Core Principles

1. **Observe → Plan → Act → Evaluate**: Always understand the current state before acting
2. **Use aim_id for clicks**: Never click without first aiming and confirming position
3. **Prefer browser tools for web**: Use browser_* tools instead of desktop GUI for web tasks
4. **Verify results**: After each action, check if it succeeded before proceeding

## Desktop GUI Control Workflow

**Step 1: Observe** - Understand current screen state
```python
screenshot()  # View full screen with coordinate grid
```

**Step 2: Aim** - Lock onto target with precision
```python
mouse(action='aim', x=600, y=400)  # Returns aim_id + zoomed view
```

**Step 3: Verify** - Read crosshair position
- Crosshair at origin (0) = on target → click
- Crosshair off-target → read delta from axis ticks, re-aim

**Step 4: Execute** - Click with confidence
```python
mouse(action='click', aim_id='...')  # Execute click
```

## Browser Automation Workflow

**Prefer CSS selectors over coordinates when possible:**
```python
browser_navigate(url='https://...')
browser_click(selector='button.submit')
browser_type(selector='input[name="q"]', text='...')
```

## Quick Reference

| Task | Workflow |
|------|----------|
| Desktop GUI | screenshot → aim → verify → click |
| Web browsing | browser_navigate → browser_click/type |
| File operations | read_file, write_file |
| System commands | run_command |
| Remember info | memory_save, memory_recall |

## Error Recovery

- Tool failed? Read error message and try alternative approach
- Click missed? Re-aim with higher zoom (4-8)
- Page not loading? Check URL and wait_until parameter
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
