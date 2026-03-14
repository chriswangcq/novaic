# Context Summary

> 指挥中心 — 近期上下文与关键结论汇总

---

## 1. 架构总览

### 1.1 设计理念

- **Master-Driven**：Gateway 为协调中心，不直接执行任务
- **Saga/Task 三层**：Saga 编排流程，Task 执行原子操作
- **B2 Split**：Gateway 管 Agent/SubAgent，Runtime Orchestrator 管 Runtime；Gateway 不持有 agent_runtimes

### 1.2 服务与端口

| 服务 | 端口 | 职责 |
|------|------|------|
| Gateway | 19999 | API 网关、Agent/SubAgent、Chat、SSE |
| Tools Server | 19998 | 工具执行、MCP 集成、Runtime 上下文 |
| Queue Service | 19997 | Task/Saga 队列、任务分发 |
| File Service (storage-a) | 19996 | 文件存储 |
| Tool Result Service (storage-b) | 19994 | 工具结果存储 (TRS) |
| Runtime Orchestrator | 19993 | Runtime API、主 Agent 流程 |
| VMControl | 8080 | QEMU、Android 设备控制 |

### 1.3 主 Agent 任务执行路径

- **Task Worker** 在 **agent-runtime** 中运行（非 RO）
- 工具执行：`tool_handlers` → `MCPBusiness.execute_tool` → Tools Server
- RO 提供 Runtime API（create、context、status 等），不直接跑 Task

---

## 2. Saga 流程（6 个）

### 2.1 message_process

```
message.claim → message.route → DECISION → runtime_start (如需)
```

### 2.2 runtime_start

```
runtime.create → mcp.create → subagent.set_awake → react_think
```

### 2.3 react_think

```
context.read → llm.call → context.append → DECISION(提取 tool_calls) → react_actions
```

### 2.4 react_actions

```
runtime.update_phase(waiting_actions) → PARALLEL tool.execute → PARALLEL context.append
→ runtime.check_new_messages → DECISION → react_think 或 runtime_complete
```

### 2.5 runtime_complete

```
runtime.set_status(completed) → runtime.generate_simple_summary → subagent.set_sleeping
→ mcp.destroy → summarize
```

### 2.6 summarize

```
llm.call_hot_cold_summary → summary.add_to_hrl → summary.merge_history_if_needed
```

---

## 3. 工具执行完整链

```
1. Task Worker 认领 tool.execute
2. tool_handlers.handle_tool_execute (agent-runtime 或 RO)
3. MCPBusiness.execute_tool
   → POST Tools Server /internal/runtimes/{runtime_id}/tools/call
4. Tools Server api.call_tool
   → ToolExecutor.execute (executor.py)
   → 内置工具: Gateway API 或 vmcontrol
   → 外部工具: MCP client
5. 结果处理:
   → api.py: create_from_raw(actual_result) 推 TRS
   → 返回 CallToolResponse(success, result_id, error)
6. tool_handlers 广播 tool complete，返回 result_id
7. react_actions: context.append 存 result_id（有则用，无则兜底创建）
```

**关键文件**：
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-agent-runtime/task_queue/business/mcp.py`
- `novaic-tools-server/tools_server/api.py` (call_tool)
- `novaic-tools-server/tools_server/executor.py`

---

## 4. TRS 存储逻辑

### 4.1 三要素格式

```python
{
  "text": "...",
  "files_created": [{url, filename, modality}],
  "display_files": [{url, filename, modality}]
}
```

### 4.2 _parse_tool_result 分支

- 统一格式：`display_files` / `files_created`
- 旧格式：`files` → 作为 display_files（**要求每项有 url**）
- MCP 格式：`content` / `_mcp_content`
- 兜底：`json.dumps(raw)`，display_files=[]

### 4.3 常见坑

- 工具返回的 `files` 若为 `{name, path, is_dir, size}` 等无 `url` 格式，会被误当 display_files → TRS 校验失败（mobile_file_list 已删除）
- 工具失败时也需推 TRS 存 error，否则 LLM 拿不到 result_id

---

## 5. 近期修复（已落地）

### 5.1 subagent_query 误判 success=False

- **根因**：`_handle_response` 用 `"error" not in result` 推断 success；subagent status 的 `error` 是业务数据（子任务失败原因），非 API 失败
- **修复**：无 `success` 时默认 `success=True`（HTTP 200 即请求成功）
- **文件**：`novaic-tools-server/tools_server/executor.py`

### 5.2 工具失败时 result_id 丢失

- **根因**：Tools Server 正确返回 result_id，但 agent-runtime 的 `MCPBusiness.execute_tool` 在 success=False 时不传 result_id；tool_handlers 在 success=False 时返回 result_id=None；react_actions 会重复创建 TRS
- **修复**：
  - MCPBusiness 失败分支传 `result_id=result.get("result_id")`
  - tool_handlers 无论 success 都返回 `result.result_id`
  - 广播时：有 result_id 就传（不再要求 success and result_id）
  - react_actions：有 result_id 时不再 `create_from_raw` 兜底
- **文件**：agent-runtime、RO 的 mcp.py、tool_handlers.py、react_actions.py

### 5.3 need_rest 与 check_and_clear_need_rest

- **根因**：RO 从 RO DB 读 need_rest，而 runtime_rest 只写 Gateway subagents.need_rest
- **修复**：RO 与 agent-runtime 均通过 Gateway `check_and_clear_need_rest` 统一处理
- **文件**：handle_check_new_messages 相关

---

## 6. 工具错误分析（待修）

### 6.1 subagent_cancel — 执行失败

**根因**：设计如此，仅对 `running` 子任务有效。对 completed/failed/cancelled/sleeping 会返回 `success: False, reason: "SubAgent is not running (status: xxx)"`。

**可能改进**：对「SubAgent is not running」返回 success=True + message 说明已结束；或工具描述中明确仅对 running 调用

### 6.2 VM 工具（browser_get_tabs, browser_close_tab, directory_snapshot, launch_app）

**原因**：依赖 VM 内 novaic-mcp-vmuse，VM 未启动或未部署则不可用。  
**状态**：实现问题，暂不修。

---

## 7. 数据库与日志

### 7.1 数据目录（macOS）

```
~/Library/Application Support/com.novaic.app/
├── gateway.db              # Gateway: agents, subagents, execution_logs
├── runtime_orchestrator.db # RO: agent_runtimes (B2 下 RO 持有)
├── queue.db                # Task/Saga 队列
├── tool_results.db         # TRS 存储
├── logs/
│   ├── gateway-YYYYMMDD.log
│   ├── tools-server.log
│   ├── runtime-orchestrator.log
│   ├── task-worker-YYYYMMDD.log
│   ├── saga-worker-YYYYMMDD.log
│   ├── tool-result-service.log
│   └── queue-service.log
└── config/
```

### 7.2 调试日志标签

```
[ToolsAPI.call_tool]     # Tools Server 入口、TRS 结果
[TRSSDK.create]          # TRS create 请求与返回
[TRSSDK.create_from_raw] # TRS 解析入口
[tool_handlers]          # Task Handler 返回
[MCPBusiness.execute_tool] # Tools Server 响应
```

### 7.3 常用 SQL

```bash
DATA_DIR=~/Library/Application\ Support/com.novaic.app

# 任务
sqlite3 "$DATA_DIR/queue.db" "SELECT id, topic, status, error FROM tq_tasks ORDER BY created_at DESC LIMIT 10;"

# Saga
sqlite3 "$DATA_DIR/queue.db" "SELECT id, saga_type, status, current_step, error FROM tq_sagas ORDER BY created_at DESC LIMIT 5;"

# 执行日志
sqlite3 "$DATA_DIR/gateway.db" "SELECT id, kind, status, event_key, result_data FROM execution_logs ORDER BY id DESC LIMIT 10;"

# SubAgent
sqlite3 "$DATA_DIR/gateway.db" "SELECT subagent_id, agent_id, type, status FROM subagents;"
```

---

## 8. 构建与脚本

### 8.1 完整构建

```bash
cd novaic-app
./scripts/build-dmg.sh
```

产物：`src-tauri/target/release/bundle/dmg/NovAIC_0.x.x_aarch64.dmg`

### 8.2 添加 Agent 到 DB

```bash
cd novaic-gateway
NOVAIC_DATA_DIR=~/Library/Application\ Support/com.novaic.app python scripts/add_agent_a2.py
# 可选: --name A2, --agent-id xxx
```

---

## 9. 关键概念速查

| 概念 | 说明 |
|------|------|
| Main SubAgent | `main-{agent_id[:8]}`，每个 Agent 一个 |
| Sub SubAgent | `sub-{uuid}`，子任务派生产生 |
| result_id | 每个 tool_call 必须有，供 LLM 从 TRS 取内容 |
| need_rest | 主 Agent 完成一轮后需休息，由 runtime_rest 设置，check_new_messages 检查 |
| lazy_hydrate | Tools Server 无 runtime 时从 Gateway 拉取 agent_id 等 |

---

## 10. 常见坑与提醒

1. **B2 Split**：Gateway 与 RO 各管一块，Internal API 可能 proxy 到 RO
2. **主 Agent 的 tool_handlers 在 agent-runtime**，不在 RO
3. **result_id 必传**：失败时也需推 TRS，否则 context.append 会抛异常
4. **TRS display_files**：必须是 `{url, filename, modality}`，否则 Pydantic 校验失败
5. **subagent_id 格式**：Main 为 `main-{agent_id[:8]}`，Sub 为 `sub-{uuid}`
