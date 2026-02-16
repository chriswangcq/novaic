# NovAIC 超时配置说明

## 核心设计原则

**工具执行无超时限制，超时管理由心跳机制统一控制。**

---

## 🔄 心跳超时机制（主要控制）

### 工作原理
1. **Task Worker** 在执行任务时，每 **10 秒**发送一次心跳
2. **Saga Worker** 在执行 Saga 时，每 **10 秒**发送一次心跳
3. **Health Worker** 每 **30 秒**检查所有运行中的任务/Saga
4. 如果任务的 `heartbeat_at` 超过阈值，自动重置为 `pending`（重试）

### 心跳超时阈值

| 类型 | 超时时间 | 配置位置 |
|------|---------|---------|
| **Task** | 120 秒 | `health_worker_sync.py:64` |
| **Saga** | 600 秒 (10分钟) | `health_worker_sync.py:65` |

### 优势
- ✅ **工具可以执行任意时长**（只要 Worker 在发心跳）
- ✅ **Worker 崩溃时自动恢复**（心跳停止 → 超时 → 重试）
- ✅ **避免固定超时的僵化问题**

---

## 🚫 已移除的 HTTP 超时

### Tools Server → Gateway/VMControl/Mobile
```python
# tools_server/executor.py
httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0,
        read=None,      # ✅ 无限制（原 60秒）
        write=30.0,
        pool=10.0
    )
)
```

### Task Handler → Tools Server
```python
# task_queue/client.py:585
httpx.Client(timeout=None, ...)  # ✅ 无限制（原 30秒）

# task_queue/business/mcp.py:255, 333
httpx.Client(timeout=None, ...)  # ✅ 无限制（原 30秒）
```

### MCP Client → External MCP Server
```python
# mcp_client/mcp_client.py:126
httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0,
        read=None,      # ✅ 无限制（原 60秒）
        write=30.0,
        pool=10.0
    )
)
```

---

## ✅ 保留的 HTTP 超时（非工具执行）

这些超时用于控制流和元数据获取，不影响工具执行：

### 1. LLM API 调用
```python
# gateway/core/llm_client.py
DEFAULT_LLM_TIMEOUT = 300  # 5 分钟
```
**用途**：OpenAI/Anthropic API 调用  
**说明**：LLM 响应通常在 1 分钟内，300 秒足够

### 2. TRS（工具结果服务）
```python
# task_queue/utils/trs_sdk.py:180
self._timeout = 15.0  # 15 秒
```
**用途**：获取/存储工具结果  
**说明**：这是元数据操作，很快完成

### 3. Gateway/Queue Service 管理操作
```python
# task_queue/client.py
- create_runtime_tools: 30秒（创建 runtime 上下文）
- list_runtime_tools: 10秒（获取工具列表）
- destroy_runtime_tools: 10秒（删除 runtime）
```
**用途**：Runtime 管理操作  
**说明**：这些是快速的元数据操作

### 4. Watchdog/Health Worker
```python
# Watchdog: HTTP_TIMEOUT = 30秒
# Health Worker: 30秒
```
**用途**：消息监控和健康检查  
**说明**：控制流操作，不涉及工具执行

### 5. 配置获取
```python
# handlers/llm_handlers.py, handlers/summary_handlers.py
HTTP_TIMEOUT_SHORT = 10秒
```
**用途**：从 Gateway 获取 LLM 配置  
**说明**：元数据查询，很快

---

## 📊 完整超时层级

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: 心跳超时（主控）                                     │
│  - Task: 120秒没心跳 → 重试                                    │
│  - Saga: 600秒没心跳 → 重试                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: HTTP 连接（工具执行链路）                            │
│  - Task Handler → Tools Server: timeout=None ✅               │
│  - Tools Server → Gateway/VMControl: timeout=None ✅          │
│  - MCP Client → External: timeout=None ✅                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: 工具内部超时（可选参数）                             │
│  - shell_exec: timeout=30秒（可自定义）                        │
│  - mobile_shell: timeout=30秒（可自定义）                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: LLM API 超时（独立）                                 │
│  - OpenAI/Anthropic: 300秒                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 总结

### 回答你的两个问题：

**1. Task/Saga 能不能通过心跳超时？**
- ✅ **已经是心跳超时了！**
- Worker 每 10 秒发心跳
- Health Worker 检查心跳是否超时（Task 120s, Saga 600s）
- 超时后自动重试

**2. 工具能不能不设超时？**
- ✅ **已全部改为无超时！**
- 所有工具执行链路的 HTTP timeout 都改为 `None`
- 工具可以执行任意时长（只要 Worker 在发心跳）

### 当前状态
- ✅ 工具执行：无 HTTP 超时限制
- ✅ 超时管理：由心跳机制统一控制
- ✅ Worker 崩溃：自动检测和恢复
- ✅ 僵化超时：已完全消除

---

*最后更新: 2026-02-15*
