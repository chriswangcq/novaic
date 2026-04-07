# NovAIC Cortex — 架构文档

> **状态**: 当前实现（2026-04-06）  
> **服务端口**: `:19996`  
> **代码**: `novaic-cortex/novaic_cortex/`

---

## 一、核心定位

Cortex 是 NovAIC Agent 的**认知基础设施**——一个独立的 HTTP 服务，管理 Agent 的工作空间、上下文、记忆和工具执行。

Agent Runtime 通过 `CortexBridge`（HTTP 客户端）与 Cortex 交互，**不直接 import Cortex 代码**。

```
Agent Runtime (Task/Saga Workers)
  │
  │ HTTP (CortexBridge)
  ▼
Cortex (:19996)
  ├── Workspace   ← 文件系统抽象 (S3-backed)
  ├── ContextEngine ← 上下文拼装 (DFS step tree)
  ├── Recall      ← 历史记忆
  └── Sandbox     ← 命令执行
```

---

## 二、存储模型：/ro/ vs /rw/

Cortex 为每个 Agent 维护两个隔离区：

| 区域 | 管理者 | Agent 权限 | 用途 |
|------|--------|-----------|------|
| `/ro/` | **Cortex** | 只读 | scope 数据、配置、技能、知识库 |
| `/rw/` | **Agent** | 读写 | scratch 文件、agent 自由使用的空间 |

**关键：scope 是 Cortex 管理的系统对象，不是 agent 的自由文件。**

所有 scope 操作（创建、写 step、归档）在代码中使用 `_sys_*` 内部方法，绕过 `_validate_write` 的 `/rw/` ACL 检查。Agent 工具调用（如 `novaic write`）只能写入 `/rw/`。

### 2.1 目录结构

```
S3: cortex/users/{user_id}/agents/{agent_id}/
  ro/
    active/{scope_id}/          ← 活跃 scope（Cortex 管理）
      meta.json
      context.jsonl
      summary.md
      steps/
        _index.jsonl
        0000_tool_tc001.json
        0001_scope_skill-web/   ← 子 scope（嵌套）
          meta.json
          context.jsonl
          steps/_index.jsonl
          ...
    scopes/{scope_id}/          ← 归档 scope（从 active/ 移入）
    scopes/_index.jsonl         ← 归档 scope 索引
    config/
      tools/                    ← 工具 schema
    skills/                     ← 技能定义
    knowledge/                  ← 知识库
  rw/
    scratch/                    ← Agent 自由空间
```

### 2.2 S3 层级

```
S3 Bucket: novaic-s3-bucket
  Prefix: cortex/

WorkspaceRegistry 为每个 user_id 创建 S3Store:
  S3Store(bucket, prefix="users/{user_id}/")

Workspace 在 S3Store 内按 agent_id 隔离:
  agents/{agent_id}/ro/...
  agents/{agent_id}/rw/...
```

---

## 三、Scope 树

### 3.1 Scope 是什么

Scope 是 Cortex 中的**执行上下文单元**。每次 agent 被唤醒处理消息，会创建一个 root scope。Agent 调用 `skill_begin` 工具时，在当前 scope 内创建子 scope，形成树状嵌套。

### 3.2 Scope 生命周期

```
create_scope(scope_id, name, skill)
  → 写入 meta.json (phase: "executing")
  → 初始化 steps/_index.jsonl

write_step(scope_path, step_data)
  → 写入 steps/NNNN_tool_ID.json
  → 追加 steps/_index.jsonl

complete_child_scope(scope_path, summary)
  → 写入 summary.md
  → meta.json phase → "archived"

archive_root_scope(scope_id, summary)
  → 写入 summary.md
  → meta.json phase → "archived"
  → move_prefix: /ro/active/{id}/ → /ro/scopes/{id}/
  → 追加 /ro/scopes/_index.jsonl
```

### 3.3 树的维护

每个 scope 的 `steps/_index.jsonl` 是该 scope 直接子节点的**有序索引**：

```jsonl
{"seq": 0, "type": "tool", "id": "tc001", "tool": "shell", "file": "0000_tool_tc001.json"}
{"seq": 1, "type": "tool", "id": "tc002", "tool": "chat_reply", "file": "0001_tool_tc002.json"}
{"seq": 2, "type": "scope", "id": "skill-web", "name": "Build website", "file": "0002_scope_skill-web/"}
{"seq": 3, "type": "tool", "id": "tc003", "tool": "shell", "file": "0003_tool_tc003.json"}
```

- `type: "tool"` → 叶子节点，对应一个 JSON 文件
- `type: "scope"` → 子 scope 目录（复合节点）

### 3.4 活跃 scope 路径解析

`resolve_active_scope_path(root_scope_path)` 通过逐层读取 `_index.jsonl` 找到最深的 **executing** 子 scope：

```
/ro/active/root/
  └── steps/_index.jsonl → 最后一个 type:scope → skill-web/
       └── steps/_index.jsonl → 最后一个 type:scope → debug/
            └── meta.json → phase: "executing" → 这就是当前活跃 scope

写 step 时自动路由到这个最深的活跃 scope。
```

每层只需 1 次 S3 读取（`_index.jsonl`）+ 1 次 `meta.json` 读取。

---

## 四、上下文拼装：DFS Step Tree

详细设计见 `docs/context-assembly-dfs-step-tree.md`。

### 4.1 核心思想

**上下文的原子单位是 step，不是 message。**

`ContextEngine.prepare_messages_for_llm()`:

1. 读 `context.jsonl`（system prompt + user messages + recall）
2. 构建 `StepTree`（从 `_index.jsonl` 递归读取）
3. 合并：`_merge_context_and_steps()`
   - 闭合 scope → 折叠为一条 summary system message
   - 开放 scope → 展开子 step
   - tool result → 从 step 文件读取，插入到 assistant tool_calls 之后
4. 预算压缩：`budget_compact()`

### 4.2 关键类

| 类 | 文件 | 职责 |
|----|------|------|
| `StepNode` | `context_stack/step_tree.py` | step 的内存表示（tool/scope） |
| `StepTree` | `context_stack/step_tree.py` | 一个 scope 的完整 step 树 |
| `StepTreeBuilder` | `context_stack/step_tree.py` | 从 Workspace 构建 StepTree |
| `ContextEngine` | `context_stack/engine.py` | 拼装最终 messages[] |
| `budget_compact` | `context_stack/budget.py` | 三级预算压缩 |

### 4.3 context.jsonl 只存放

- System prompt
- Recall memory messages
- User messages
- Assistant messages（含 tool_calls 引用）

**不存放** tool results（由 step 文件提供）。

---

## 五、Recall（历史记忆）

`Recall` 类读取 `/ro/scopes/_index.jsonl`，为每个归档 root scope 生成一条 system message：

```python
{
    "role": "system",
    "content": "[Memory: {scope_label}]\n{summary}",
    "_metadata": {"origin": "recall", "scope_id": sid}
}
```

Agent 可通过 `novaic read /ro/scopes/{sid}/steps/_index.jsonl` 自行浏览历史 scope 的详细 step 内容。系统只在初始化时注入 summary level 的记忆。

---

## 六、API 端点

### 6.1 Agent 面向工具 (LLM tool_call → CortexBridge)

| 端点 | 用途 |
|------|------|
| `POST /v1/shell` | 执行 shell 命令 |
| `POST /v1/skill/begin` | 开启子 skill scope |
| `POST /v1/skill/end` | 结束子 skill scope |
| `GET /v1/read` | 读文件 |
| `POST /v1/write` | 写文件（限 /rw/） |
| `GET /v1/ls` | 列目录 |
| `GET /v1/recall` | 历史记忆 |
| `GET /v1/tools` | 可用工具列表 |

### 6.2 系统内部 (Agent Runtime → Cortex)

| 端点 | 用途 |
|------|------|
| `POST /v1/scope/create` | 创建 scope |
| `POST /v1/scope/end` | 归档 root scope |
| `POST /v1/context/read` | 读 context.jsonl |
| `POST /v1/context/append` | 追加 context 消息 |
| `POST /v1/context/batch` | 批量追加 |
| `POST /v1/context/prepare_for_llm` | 拼装 LLM 上下文（DFS step tree） |
| `POST /v1/context/skill_begin` | 技能开始（创建子 scope） |
| `POST /v1/context/skill_end` | 技能结束（关闭子 scope） |
| `POST /v1/context/status` | 当前上下文状态 |
| `POST /v1/steps/write` | 写 tool step |
| `POST /v1/steps/list` | 列 step 索引 |
| `POST /v1/steps/read` | 读 step 文件 |
| `POST /v1/meta/read` | 读 scope meta |
| `POST /v1/meta/update` | 更新 scope meta |

### 6.3 内部管理

| 端点 | 用途 |
|------|------|
| `POST /v1/internal/reindex` | 重建 scope 索引 |
| `POST /v1/internal/recall_messages` | Recall 系统消息 |
| `POST /v1/token` | 创建临时 Cortex token |
| `GET /health` | 健康检查 |

---

## 七、多租户

`WorkspaceRegistry` 缓存 `S3Store`（per user_id）和 `Workspace`（per user_id + agent_id）实例：

```python
registry = WorkspaceRegistry(boto3_client, bucket)
ws = registry.get_workspace(user_id, agent_id)
recall = registry.get_recall(user_id, agent_id)
```

所有 API 端点通过 request 中的 `user_id` + `agent_id` 获取对应的 Workspace 实例。

---

## 八、与 Agent Runtime 的交互

Agent Runtime 通过 `CortexBridge`（`httpx.Client`）调用 Cortex HTTP API。

### 8.1 消息处理链路

```
用户发消息 → Gateway → Watchdog → MessageProcess Saga

RuntimeStart Saga:
  1. create_scope (Cortex)
  2. session_init: system prompt + recall → context.jsonl
  3. → ReactThink

ReactThink:
  1. prepare_for_llm (Cortex ContextEngine)
  2. LLM call (Factory)
  3. save assistant message → context.jsonl
  4. → ReactActions

ReactActions:
  1. execute tools in parallel
  2. skill_begin/skill_end → Cortex scope lifecycle
  3. other tools → write_step (Cortex)
  4. → next ReactThink or terminate
```

### 8.2 关键约定

- `skill_begin` / `skill_end` 的 tool 结果**不写入** step（它们直接管理 scope 生命周期）
- 其他工具结果通过 `write_step` 写入，**不写入** `context.jsonl`
- `resolve_active_scope_path` 自动路由 step 写入到最深活跃 scope

---

## 九、关键文件速查

| 需求 | 文件 |
|------|------|
| 存储抽象 | `store.py` (CortexStore ABC)、`s3_store.py`、`aliyun_oss_s3.py` |
| 工作空间 | `workspace.py` (Workspace: scope/step/context 管理) |
| API 层 | `api.py` (FastAPI endpoints) |
| 多租户 | `registry.py` (WorkspaceRegistry) |
| 上下文引擎 | `context_stack/engine.py` (ContextEngine) |
| Step Tree | `context_stack/step_tree.py` (StepNode/StepTree/StepTreeBuilder) |
| 预算压缩 | `context_stack/budget.py` |
| 历史记忆 | `recall.py` (Recall) |
| 工具 Schema | `tool_schemas.py` |
| CortexBridge | `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` |

---

## 十、配置与部署

| 项 | 值 |
|----|-----|
| 端口 | 19996 |
| S3 Bucket | `novaic-s3-bucket` |
| S3 Prefix | `cortex/` |
| OSS Region | `oss-cn-hongkong` |
| 环境变量 | `ALIBABA_CLOUD_ACCESS_KEY_ID`、`ALIBABA_CLOUD_ACCESS_KEY_SECRET` |
| 启动命令 | `.venv/bin/python -m novaic_cortex.main_cortex` |
| 健康检查 | `GET http://localhost:19996/health` |
