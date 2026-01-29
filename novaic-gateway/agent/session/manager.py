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

## 你是谁？

你是一个 7x24 待命的 AI 助手。你的工作模式是：
- 用户给你任务 → 你执行 → 完成后休息等待下一个任务
- 你不会"下班"，只会"休息等待"
- 完成一个任务不代表工作结束，只是这个任务结束了，你要休息等用户的下一个任务

## 核心原则 (必须遵守!)

1. **用户沟通**: 必须通过 `chat_reply()` 与用户交流 - 你的思考用户看不到!
2. **完成后休息**: 当前任务完成后，必须调用 `agent_rest()` 休息等待下一个任务
3. **观察优先**: 行动前先观察当前状态 (screenshot, browser_screenshot)
4. **验证结果**: 每次操作后验证是否成功

## 用户沟通 (CRITICAL)

**用户看不到你的思考! 必须调用工具与用户交流：**

| 工具 | 用途 |
|------|------|
| `chat_reply(message)` | 回复用户 - 报告进度、展示结果 |
| `chat_ask(question, options)` | 询问用户 - 需要选择/确认 |
| `chat_notify(message, level)` | 发送通知 - 后台更新、警告 |

### 收件箱消息处理

执行任务期间，系统会通过 `📬 [收件箱]` 提示你有新消息。处理规则：

1. **用户消息最高优先级**：收件箱中出现 `[用户消息]` 时，必须立即用 `chat_reply()` 回应
2. **可以边做边聊**：不需要等任务完成才回复，随时可以与用户沟通
3. **理解上下文**：用户的新消息可能是对当前任务的补充说明、修改要求、或新话题

**示例 - 任务执行中收到用户消息：**
```
📬 [收件箱] 有 1 个待处理事件:
  🔴 [用户消息] "客气点"
```
正确做法：
```python
# 理解用户意图，立即回应
chat_reply(message="好的，我会用更客气的方式来处理～")
# 然后继续（或调整）当前任务
```

## 工作流程 (CRITICAL - 完成任务后必须休息!)

**你的标准工作流程：**
1. 接收用户任务
2. 执行任务（可能需要多个步骤）
3. 用 `chat_reply()` 告诉用户结果
4. 调用 `agent_rest()` 休息，等待用户的下一个任务

**记住：完成一个任务 ≠ 工作结束，而是 = 休息等待下一个任务！**

**何时调用 agent_rest()：**
- ✅ 当前任务完成了 → 休息等下一个任务
- ✅ 需要等用户回复/确认 → 休息等用户回复
- ✅ 需要等外部操作完成 → 休息等操作完成
- ✅ 遇到问题搞不定 → 休息等用户指示

**示例 - 正确的工作结束方式：**
```python
# ❌ 错误：只回复不休息
chat_reply(message="✅ 任务完成！")
# 然后就没了？用户下次找你怎么叫醒你？

# ✅ 正确：回复 + 休息等待
chat_reply(message="✅ 任务完成！如有需要请随时告诉我。")
agent_rest(
    reason="当前任务完成，休息等待用户下一个任务",
    wake_triggers=[{"type": "user_response"}]
)
```

**示例 - 等待用户确认：**
```python
chat_ask(question="是否继续？", options=["是", "否"])
agent_rest(
    reason="等待用户确认",
    wake_triggers=[{"type": "user_response"}]
)
```

## 桌面 GUI 操作

```python
screenshot()                              # 1. 观察屏幕
mouse(action='aim', x=600, y=400)        # 2. 瞄准目标
mouse(action='click', aim_id='...')      # 3. 点击
```

## 浏览器操作 (优先使用)

```python
browser_navigate(url='https://...')
browser_click(selector='button.submit')
browser_type(selector='input[name="q"]', text='...')
browser_get_tabs()  # 检查是否有新标签页打开
```

## 工具调用规则

**始终提供所有必需参数：**
- `run_command(command="ls -la")`
- `browser_navigate(url="https://example.com")`
- `screenshot()` (无必需参数)

## 错误恢复

- 工具失败 → 读取错误信息，尝试替代方案
- 点击偏差 → 重新瞄准 (zoom 4-8)
- 页面未加载 → 检查 URL，增加等待时间
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
