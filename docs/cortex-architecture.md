# Cortex 总览（与当前代码一致）

本文档基于 `novaic-cortex` 与 `novaic-agent-runtime` 当前主路径整理。历史方案（Recall、自动摘要、Meta skill、`subagent_rest` LLM 工具、`<PREV_SCOPE_HISTORY>`/`<PREV_SCOPE_TAIL>` 拼贴）只保留在 roadmap / historical 文档里，不应作为当前实现依据。

## 专题拆页

| 主题 | 文档 |
| --- | --- |
| Scope 创建、激活、归档、统一时间线 | [cortex/scope-lifecycle.md](cortex/scope-lifecycle.md) |
| Cortex 边界契约与 guardrail | [cortex/boundary-contract.md](cortex/boundary-contract.md) |
| `_index.jsonl`、DFS 展开/折叠、`budget_compact` | [cortex/context-timeline-and-dfs.md](cortex/context-timeline-and-dfs.md) |
| 已退役 Recall 方案说明 | [cortex/recall.md](cortex/recall.md) |
| `CortexStore`、注册表、对象键 | [cortex/storage-and-keys.md](cortex/storage-and-keys.md) |
| `Sandbox.exec`、物化与回写 | [cortex/sandbox-shell.md](cortex/sandbox-shell.md) |
| 已退役：`Compactor`、自动摘要、gem fusion | [cortex/compactor-and-gem-fusion.md](cortex/compactor-and-gem-fusion.md) |
| `EngineConfig`、`engine.json`、指标 | [cortex/engine-config-and-metrics.md](cortex/engine-config-and-metrics.md) |
| `Cortex` 运行时门面 | [cortex/runtime-facade.md](cortex/runtime-facade.md) |
| HTTP 路由清单 | [cortex/http-api.md](cortex/http-api.md) |
| 能力 JWT、`novaic` CLI | [cortex/http-api.md](cortex/http-api.md) |
| 部署启动、OSS 环境变量 | [cortex/deployment-and-startup.md](cortex/deployment-and-startup.md) |
| Agent Runtime → `prepare_for_llm` 调用链 | [cortex/agent-runtime-cortex-call-chain.md](cortex/agent-runtime-cortex-call-chain.md) |
| Runtime 全部 Cortex topic、`context.append` | [cortex/agent-runtime-all-topics.md](cortex/agent-runtime-all-topics.md) |

## 1. Cortex 是什么

Cortex 是 NovAIC Agent 的 **scope/context 基础设施**。核心职责只有两件事：

1. 维护 **LIFO scope 树**。
2. 从这棵树按 DFS 拼装 **LLM context**。

当前 Cortex 还提供 Workspace、Sandbox 与能力 JWT。它不负责用户画像、业务任务系统、记忆推断、自动总结、wake summary、业务代理，也不从 `im_reply` 或聊天文本猜长期记忆。

## 2. 当前 scope 模型

Agent Runtime 在 `session_init` 中确保一个长期存在的 agent-root scope：

- root id 形如 `agent-root-{subagent_id}`。
- 每次 wake 在 agent-root 下创建一个 child wake scope。
- wake scope 是本轮真实工作容器。
- LLM 可见的 Active scope stack 隐藏 agent-root，只显示当前 wake 和 wake 内子 skill。

本轮结束路径：

1. LLM 先通过 `im_reply` 回复用户。
2. LLM 再按 Active scope stack 调用 `skill_end(scope_id=<栈顶>, report=...)`。
3. Cortex 将 `report` 原样写入被关闭 scope 的 `summary.md`。
4. 栈空后 Runtime 触发 `wake_finalize` 做结构性收尾。

`wake_finalize` 不生成 summary，不拼接聊天内容，不推断记忆。结构性 `/v1/scope/end` 也拒绝非空 `report`。

## 3. LLM context 拼装

`ContextEngine.prepare_messages_for_llm()` 从 agent-root scope 开始：

- 读 `context.jsonl`。
- 构建 Step Tree。
- 对开放 scope 做 DFS 展开。
- 对已关闭且 `summary.md` 非空的 scope 折叠为 system message。
- 插入 tool result。
- 调用 `budget_compact` 控制 token 预算。

核心规则：

```text
open scope      -> expand children
closed scope    -> fold to "[Skill '<name>' completed]\n<summary.md>"
blank summary   -> suppress fold content
agent-root      -> traversal entry, not shown in Active stack
```

## 4. 源码模块地图

| 模块 | 职责 |
| --- | --- |
| `api.py` | FastAPI 路由：scope、context、steps、meta、shell、token、health |
| `registry.py` | `WorkspaceRegistry`：按 user 缓存 `S3Store`，按 `(user, agent)` 缓存 `Workspace` |
| `workspace.py` | `/ro` `/rw` ACL、scope 生命周期、step/context CRUD |
| `context_stack/engine.py` | `ContextEngine`：合并 `context.jsonl` 与 Step Tree，输出 LLM messages |
| `context_stack/step_tree.py` | `StepTreeBuilder` 与 scope fold 渲染 |
| `context_stack/budget.py` | token 预算压缩 |
| `sandbox.py` | 物化 workspace → shell → 回写 `/rw` |
| `runtime.py` | 旧门面与 CLI 辅助能力；当前 LLM context 主路径在 `api.py` + `ContextEngine` |
注意：当前源码目录没有 `recall.py`，也没有 `/v1/recall` / `/v1/internal/recall*` 主路径。

## 5. HTTP API 关键点

- `POST /v1/context/prepare_for_llm`：返回 `messages`、`stack`、`estimated_tokens`。
- `POST /v1/context/skill_begin`：在当前 active scope 下开子 scope，id 全局唯一。
- `POST /v1/context/skill_end`：只能关闭当前栈顶 scope，`report` 写为该 scope 的 `summary.md`。
- `POST /v1/scope/end`：结构性归档/关闭 API；非空 `report` 被拒绝。
- `POST /v1/steps/write`：写工具结果 step。
- `POST /v1/scope/append_input`：写用户输入 env step。

完整清单见 [cortex/http-api.md](cortex/http-api.md) 与 `novaic-cortex/novaic_cortex/api.py`。

## 6. Runtime 衔接

Agent Runtime 通过 `CortexBridge` 调 Cortex HTTP API：

- `runtime_handlers.py`：创建/确保 agent-root 与当前 wake scope。
- `cortex_handlers.py`：封装 `prepare_for_llm`、`skill_begin`、`skill_end`、`scope_end` 等 topic。
- `react_think.py`：准备 LLM 调用，保存 assistant message。
- `react_actions.py`：执行 tool calls，写 tool step；若 stack 非空继续 think，给 LLM 关闭 scope 的机会。
- `wake_finalize.py`：Runtime cleanup only，不创建 `summary.md`。

## 7. 已确认退役/不属于 Cortex 的东西

- 自动总结、Compactor、Gem Fusion。
- 独立 Recall 注入通道。
- 用户画像与业务任务系统。
- 记忆推断。
- wake summary。
- 从 `im_reply` 或聊天文本猜长期记忆。
- 多条并行摘要通路。
- Meta scope / Meta skill。
- LLM 可见的 `subagent_rest` 工具。

## 8. 相关链接

- [architecture/cortex.md](architecture/cortex.md)
- [architecture/agent-pipeline.md](architecture/agent-pipeline.md)
- [cortex/scope-lifecycle.md](cortex/scope-lifecycle.md)
- [cortex/context-timeline-and-dfs.md](cortex/context-timeline-and-dfs.md)
