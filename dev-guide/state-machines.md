# NovAIC 状态机文档

本文档描述系统中各实体的状态及其转换关系。

## ID 命名规范

| ID 类型 | 格式 | 示例 | 说明 |
|---------|------|------|------|
| `agent_id` | UUID | `56d7ec79-2ce5-40d8-bb59-03409e22ed59` | Agent 唯一标识 |
| `subagent_id` | `main-xxx` / `sub-xxx` | `main-56d7ec79`, `sub-a1b2c3` | SubAgent 标识，前缀区分类型 |
| `runtime_id` | `rt-xxx` | `rt-c0577d267490` | Runtime 执行环境标识 |
| `round_id` | `round-N` | `round-1`, `round-42` | ReACT 循环轮次 |
| `task_id` | `task-xxx` | `task-3092c140e38b` | Pipeline 任务标识 |

**MCP 路径映射：**
- Runtime MCP: `/mcp/runtime/{runtime_id}/`
- Aggregate MCP: `/mcp/aggregate/{runtime_id}/`

---

## 1. SubAgent 状态

SubAgent 是执行任务的主体，每个 Agent 有一个 Main SubAgent，可以有多个 Sub SubAgent。

### 状态列表

| 状态 | 说明 | 适用类型 |
|------|------|----------|
| `sleeping` | 休眠中，等待唤醒 | Main, Sub |
| `awaking` | 正在唤醒（中间状态） | Main, Sub |
| `awake` | 已唤醒，有 active runtime | Main, Sub |
| `summarizing` | 正在总结（预留） | Main, Sub |
| `running` | 运行中（async SubAgent） | Sub only |
| `completed` | 已完成 | Sub only |
| `failed` | 失败 | Main, Sub |
| `cancelled` | 已取消 | Sub only |

### 状态转换图

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
┌──────────┐   Monitor    ┌──────────┐  RuntimeCollector  ┌──────────┐
│ sleeping │ ──────────▶  │ awaking  │ ─────────────────▶ │  awake   │
└──────────┘  (CAS唤醒)   └──────────┘   (runtime ready)  └──────────┘
     ▲                          │                              │
     │                          │                              │
     │ SummarizeCollector       │ RuntimeCollector             │ runtime_rest
     │ (runtime completed)      │ (MCP failed)                 │ 或 runtime完成
     │                          │                              │
     │                          ▼                              │
     └──────────────────────────┴──────────────────────────────┘
```

### 关键转换规则

| 转换 | 触发条件 | 触发者 | CAS |
|------|----------|--------|-----|
| sleeping → awaking | 用户消息 + wake_triggers 匹配 | Monitor | ✅ |
| failed → awaking | 用户消息（重试） | Monitor | ✅ |
| awaking → awake | Runtime + MCP 创建成功 | RuntimeCollector (set_subagent_awake) | ❌ |
| awaking → sleeping | MCP 创建失败 | RuntimeCollector (set_subagent_sleeping) | ❌ |
| awake → sleeping | Runtime 完成/休息 | SummarizeCollector (set_subagent_sleeping) | ❌ |

### v18 修复记录

**问题 1：** `update_subagent(status="awake")` 不生效，导致 SubAgent 一直是 `awaking` 状态。
**原因：** `update_subagent` API 不处理 `status` 字段。
**修复：** 使用专门的 `set_subagent_awake()` 方法。

**待修复：** Monitor 应同时检查 `has_active_runtime()` 以防止重复创建 Runtime。

### v19 修复记录

**问题 1：** `runtime_rest` 后不进入 complete，继续触发下一轮 thinking。
**原因：** ActionsCollector 在函数开头获取 runtime 状态，但 `runtime_rest` 在 tool_call 执行时才设置 `status='resting'`，导致检查时用的是旧状态。
**修复：** ActionsCollector 在检查 resting 前重新获取 runtime 状态。

**问题 2：** RuntimeLauncher 失败时留下残留的 Runtime 记录（mcp_url 为空）。
**原因：** RuntimeLauncher 先创建 Runtime 记录，再创建 MCP。如果 MCP 创建失败，Runtime 记录没有被清理。
**修复：** 
1. 添加 try-catch，MCP 创建失败时回滚删除 Runtime 记录（原子性）
2. 添加 `RetryableError` 异常类，失败时任务释放回 pending 而非标记 failed
3. 添加 `release_task` API 让任务可被重新 claim

**任务重试机制：**
- `RetryableError`：可重试的瞬态错误（如 MCP 创建失败）
- 任务状态：`claimed` → `pending`（通过 release_task）
- 任务可被其他 worker 重新 claim 并重试

---

## 2. Runtime 状态

Runtime 是 SubAgent 的执行环境，一个 SubAgent 同一时间应该只有一个 active runtime。

### 状态列表

| 状态 | 说明 | 下一步 |
|------|------|--------|
| `active` | 正在工作 | 继续 ReACT 循环 |
| `resting` | Agent 主动休息，等待用户回复 | 无新消息 → summarize → completed |
| `completed` | 本次会话结束 | SubAgent → sleeping |
| `failed` | 出错了 | SubAgent → sleeping |

### Phase（ReACT 循环内的小状态）

Phase 是 `active` 状态内部的流转状态，用于跟踪当前在 ReACT 循环的哪一步：

```
need_think → waiting_think → waiting_actions → need_think → ...
                                    ↓
                              (工具执行完)
                                    ↓
                         有结果? → 回到 need_think
                         无结果? → completed
```

| Phase | 在干嘛 |
|-------|--------|
| `need_think` | 该让 LLM 想一想了 |
| `waiting_think` | LLM 正在想 |
| `waiting_actions` | 工具正在执行 |
| `completed` | ReACT 循环结束 |

**v18 修复：**
- ActionsCollector 检测到 Runtime status = `resting` 且无新消息时，直接进入 summarize
- 避免 runtime_rest 后多余的 think 轮次

### 状态转换图

```
┌──────────┐  RuntimeLauncher  ┌────────────────────────────────────────────┐
│  (新建)  │ ───────────────▶  │               active                       │
└──────────┘                   │  ┌───────────┐     ┌─────────────────────┐ │
                               │  │need_think │ ◀──▶│ waiting_actions     │ │
                               │  └───────────┘     └─────────────────────┘ │
                               └─────────────────────────────────────────────┘
                                        │                    │
                     runtime_rest       │                    │ think 失败
                     (Agent 决定休息)   │                    │
                                        ▼                    ▼
                               ┌──────────┐          ┌──────────┐
                               │ resting  │          │  failed  │
                               └──────────┘          └──────────┘
                                        │
                     SummarizeCollector │
                     (完成总结)         │
                                        ▼
                               ┌──────────┐
                               │completed │
                               └──────────┘
```

### 关键转换规则

| 转换 | 触发条件 | 触发者 |
|------|----------|--------|
| (新建) → active | RuntimeLauncher 创建 | RuntimeLauncher |
| active → resting | Agent 调用 runtime_rest | runtime_rest 工具 |
| active → failed | 执行错误 | 各种 Collector |
| active → completed | 正常完成 | SummarizeCollector |
| resting → completed | 总结完成 | SummarizeCollector |

---

## 3. Message 状态

消息有两套状态系统：

### read 字段（Agent 消费用）

| 值 | 说明 |
|----|------|
| 0 | 未读，等待 Agent 处理 |
| 1 | 已读，已被 Agent 处理 |

### status 字段（Monitor 消费用）

| 状态 | 说明 |
|------|------|
| `sending` | 待处理，等待 Monitor 认领 |
| `sent` | 已确认，Monitor 已处理 |

### 状态转换图

```
┌──────────────┐   用户发消息    ┌──────────┐   Monitor claim   ┌──────────┐
│   (不存在)   │ ─────────────▶  │ sending  │ ────────────────▶ │   sent   │
└──────────────┘                 │ read=0   │     (CAS)         │  read=0  │
                                 └──────────┘                   └──────────┘
                                                                      │
                                                                      │ Agent 处理
                                                                      │
                                                                      ▼
                                                                ┌──────────┐
                                                                │   sent   │
                                                                │  read=1  │
                                                                └──────────┘
```

---

## 4. Pipeline Task 状态

Pipeline 任务是系统内部的工作单元。

### 状态列表

| 状态 | 说明 |
|------|------|
| `pending` | 等待认领 |
| `claimed` | 已被 Worker 认领 |
| `done` | 已完成 |
| `failed` | 执行失败 |

### 状态转换图

```
┌──────────┐   Worker claim   ┌──────────┐   执行完成   ┌──────────┐
│ pending  │ ───────────────▶ │ claimed  │ ──────────▶  │   done   │
└──────────┘      (CAS)       └──────────┘              └──────────┘
                                   │
                                   │ 执行失败
                                   ▼
                              ┌──────────┐
                              │  failed  │
                              └──────────┘
```

---

## 5. 完整执行流程

```
用户发消息
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Message: sending → sent                                                  │
│ (Monitor claim)                                                          │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ SubAgent: sleeping → awaking                                             │
│ (Monitor CAS 唤醒)                                                       │
│                                                                          │
│ ⚠️ 应该同时检查 has_active_runtime()！                                   │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ runtime_launcher → runtime_collector                                     │
│ - 创建 Runtime (active, need_think)                                      │
│ - 创建 MCP servers                                                       │
│ - SubAgent: awaking → awake                                              │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ReACT 循环                                       │
│                                                                          │
│  think_launcher ──▶ think (LLM) ──▶ think_collector                      │
│       ▲                                    │                             │
│       │                                    ▼                             │
│       │                          ┌─────────────────┐                     │
│       │                          │ 有 actions?     │                     │
│       │                          └─────────────────┘                     │
│       │                            │ Yes      │ No                       │
│       │                            ▼          ▼                          │
│       │              actions_launcher    summarize_launcher              │
│       │                    │                                             │
│       │                    ▼                                             │
│       │              tool_call (执行工具)                                │
│       │                    │                                             │
│       │                    ▼                                             │
│       │              actions_collector                                   │
│       │                    │                                             │
│       │   has_results      │      has_done                               │
│       └────────────────────┘          │                                  │
│                                       ▼                                  │
│                              summarize_launcher                          │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ summarize_collector                                                      │
│ - Runtime: active → completed                                            │
│ - SubAgent: awake → sleeping                                             │
│                                                                          │
│ ⚠️ 设置 sleeping 前应该检查是否还有其他 active runtime！                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 已修复和待修复的问题

### ✅ 已修复: SubAgent 状态设置失效 (v18)

**现象：** SubAgent 一直是 `awaking` 状态，Health 服务超时后重置为 `sleeping`，导致重复创建 Runtime。

**根本原因：** `update_subagent(status="awake")` API 不处理 `status` 字段。

**修复：**
- 添加 `/internal/subagents/{agent_id}/{subagent_id}/awake` API endpoint
- 添加 `sdk.subagent.set_awake()` 方法
- 添加 `gateway_client.set_subagent_awake()` 方法
- RuntimeCollector 使用 `set_subagent_awake()` 而不是 `update_subagent(status="awake")`

### ✅ 已修复: runtime_rest 后多余的 think (v18)

**现象：** Agent 调用 runtime_rest 后，还会触发一轮额外的 think。

**修复：**
- runtime_rest 工具设置 Runtime status = `resting`
- ActionsCollector 检测到 status = `resting` 且无新消息时，直接进入 summarize

### ⏳ 待修复: Monitor 应检查 has_active_runtime

**现象：** 理论上仍可能重复创建 Runtime（虽然上述修复已解决主要问题）。

**建议修复位置：** `services/monitor_worker.py` 第 139 行后添加：

```python
# 检查是否已有 active runtime（双保险）
has_active = await self.client.has_active_runtime(agent_id, subagent_id)
if has_active:
    self._log(f"SubAgent {subagent_id} already has active runtime, skip")
    return
```

---

## 7. 状态机设计原则

1. **CAS 操作用于并发控制：** 状态转换涉及多个 Worker 时使用 CAS
2. **中间状态防止重入：** 如 `awaking` 防止多个 Monitor 同时唤醒
3. **幂等性：** 使用 idempotency_key 防止重复任务
4. **状态应与资源对应：** SubAgent 状态应准确反映是否有 active runtime
