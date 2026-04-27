# Cortex 总览（与代码一致）

本文档基于 `**novaic-cortex**` 子模块源码整理，并与 `**novaic-agent-runtime**` 中 `cortex.prepare_llm_context` 调用链对照。历史设计长文仍可从父仓 **[historical-doc-links.md](historical-doc-links.md)** 用 `git show` 查看。

## 专题拆页（更细）


| 主题 | 文档 |
| --- | --- |
| Scope 创建、激活、归档、统一时间线 | **[cortex/scope-lifecycle.md](cortex/scope-lifecycle.md)** |
| Cortex 边界契约与 guardrail | **[cortex/boundary-contract.md](cortex/boundary-contract.md)** |
| `_index.jsonl`、DFS 展开/折叠、`budget_compact` | **[cortex/context-timeline-and-dfs.md](cortex/context-timeline-and-dfs.md)** |
| `Recall` 与全局记忆索引 | **[cortex/recall.md](cortex/recall.md)** |
| `CortexStore`、注册表、对象键 | **[cortex/storage-and-keys.md](cortex/storage-and-keys.md)** |
| `Sandbox.exec`、物化与回写 | **[cortex/sandbox-shell.md](cortex/sandbox-shell.md)** |
| 已退役：`Compactor`、自动摘要、gem fusion | **[cortex/compactor-and-gem-fusion.md](cortex/compactor-and-gem-fusion.md)** |
| `EngineConfig`、`engine.json`、指标 | **[cortex/engine-config-and-metrics.md](cortex/engine-config-and-metrics.md)** |
| `Cortex` 运行时门面 | **[cortex/runtime-facade.md](cortex/runtime-facade.md)** |
| HTTP 路由清单 | **[cortex/http-api.md](cortex/http-api.md)** |
| JWT、`BusinessProxy`、`novaic` CLI | **[cortex/proxy-cli-auth.md](cortex/proxy-cli-auth.md)** |
| `log_cortex`、测试目录 | **[cortex/observability-and-tests.md](cortex/observability-and-tests.md)** |
| 部署启动、OSS 环境变量 | **[cortex/deployment-and-startup.md](cortex/deployment-and-startup.md)** |
| `/ro`/`/rw` ACL、`_sys_*` | **[cortex/workspace-acl-and-sys-writes.md](cortex/workspace-acl-and-sys-writes.md)** |
| 内置工具 schema、技能安装 | **[cortex/builtin-tools-and-skills.md](cortex/builtin-tools-and-skills.md)** |
| Hooks、协议、StepTree、压缩建议 | **[cortex/extension-points.md](cortex/extension-points.md)** |
| Entangled、`fs://`、TRS 等 | **[cortex/satellite-modules.md](cortex/satellite-modules.md)** |
| `budget_compact` 算法（micro/warm/emergency） | **[cortex/budget-compact-algorithm.md](cortex/budget-compact-algorithm.md)** |
| Agent Runtime → `prepare_for_llm` 调用链 | **[cortex/agent-runtime-cortex-call-chain.md](cortex/agent-runtime-cortex-call-chain.md)** |
| Runtime 全部 Cortex topic、`context.append` | **[cortex/agent-runtime-all-topics.md](cortex/agent-runtime-all-topics.md)** |
| `steps/_index.jsonl` 与磁盘载荷 | **[cortex/step-index-and-payload-schema.md](cortex/step-index-and-payload-schema.md)** |
| 会话 `meta.json` | **[cortex/session-meta-json.md](cortex/session-meta-json.md)** |
| Internal API 请求/响应摘要 | **[cortex/internal-api-schemas.md](cortex/internal-api-schemas.md)** |
| `/v1/proxy/{command}` → Business | **[cortex/proxy-gateway-routes.md](cortex/proxy-gateway-routes.md)** |
| 源码中的设计稿引用 | **[cortex/design-doc-links.md](cortex/design-doc-links.md)** |
| 索引与学习路径 | **[cortex/README.md](cortex/README.md)** |


---

## 1. Cortex 是什么

**Cortex** 是 NovAIC Agent 的**scope/context 基础设施**：它的核心职责只有两件事，维护 **LIFO scope 树**，并从这棵树拼装 **LLM context**。在对象存储（生产为 **阿里云 OSS**）上维护每个 `(user_id, agent_id)` 的 **Workspace**（逻辑路径 `/ro/*` 与 `/rw/*`），提供：

- **Scope / Skill** 生命周期与 **步骤时间线**（`steps/_index.jsonl` + 单步 JSON 文件）；
- **上下文拼装**：`ContextEngine.prepare_messages_for_llm` 按时间线做 **DFS** 式展开（开放子 scope 递归，已归档 scope 折叠为摘要），再经 `**budget_compact`** 做 token 预算压缩；
- **Recall**：历史 root scope 摘要读取能力；主 LLM 路径不再依赖独立 wake summary 通道；
- **Scope 归档**：生命周期容器归档不生成 summary；只有 LLM 显式 child `skill_end(report=...)` 写该 child 的 `summary.md`；
- **Sandbox**：每次 `shell` 在临时目录物化 `/ro`+/`rw`，执行子进程，再把 `**/rw` 变更**写回存储；
- **BusinessProxy（遗留代理面）**：仅保留 CLI 的 `chat`、设备/VM、subagent 代理命令；`memory`、`notebook`、`task`、`search` 已退出 Cortex 代理面。

运行时对外是 **单一 FastAPI 应用**（`novaic_cortex.api:app`），默认监听 `**0.0.0.0:19996`**（`CORTEX_HOST` / `CORTEX_PORT`）。

---

## 2. 入口、启动与依赖


| 项           | 说明                                                                                                                                                             |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Uvicorn 入口  | `python -m novaic_cortex.main_cortex` 或 `uvicorn novaic_cortex.main_cortex:app`                                                                                |
| 启动钩子        | `main_cortex.py`：`startup` 时创建 OSS boto 客户端、`WorkspaceRegistry`、`BusinessProxy` 并注入全局                                                                           |
| 对象存储        | 环境变量 `**ALIBABA_CLOUD_ACCESS_KEY_ID`**、`**ALIBABA_CLOUD_ACCESS_KEY_SECRET`**；`**NOVAIC_OSS_ENDPOINT**`、`**NOVAIC_OSS_REGION**`、`**NOVAIC_OSS_BUCKET**`（默认值见代码） |
| Business 侧信任 | `**BUSINESS_INTERNAL_URL**`（默认如 `http://127.0.0.1:19998`）、`**CORTEX_INTERNAL_KEY**`（`X-Internal-Key`）                                                           |


---

## 3. 源码模块地图（`novaic_cortex/`）


| 模块                               | 职责                                                                                                                     |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `**api.py**`                     | 唯一 FastAPI `app`，注册全部 HTTP 路由（无独立 `APIRouter` 文件）                                                                      |
| `**main_cortex.py**`             | Uvicorn 启动、OSS/registry/proxy 注入                                                                                       |
| `**registry.py**`                | `WorkspaceRegistry`：按 user 缓存 `S3Store`，按 `(user, agent)` 缓存 `Workspace` 与 `Recall`                                    |
| `**workspace.py**`               | `Workspace`：`/ro` `/rw` ACL、scope 创建/激活/归档、`**_sys_***` 系统写、步骤与 `context.jsonl`                                        |
| `**store.py` / `s3_store.py**`   | `CortexStore` 抽象与 S3 实现（测试可用 `MemoryStore` / `LocalFileStore`）                                                         |
| `**context_stack/engine.py**`    | `ContextEngine`：`prepare_messages_for_llm`、按 `_index.jsonl` 渲染消息                                                       |
| `**context_stack/step_tree.py**` | `StepTreeBuilder`、`StepNode`：树形建模（与 engine 时间线渲染互补）                                                                    |
| `**context_stack/budget.py**`    | `budget_compact`：紧急/温和压缩、按轮截断 tool 内容                                                                                  |
| `**context_stack/types.py**`     | 类型与 token 计数相关定义                                                                                                       |
| `**recall.py**`                  | `Recall`：读 `/ro/scopes/_index.jsonl` + 各 `summary.md`                                                                  |
| `**sandbox.py**`                 | `Sandbox.exec`：物化 workspace → shell → 回写 `/rw`                                                                         |
| `**runtime.py**`                 | `**Cortex**` 门面：`tool_read` / `tool_write` / `tool_shell`、`skill_begin` / `skill_end`、`prepare_system_prompt`（Recall）等 |
| `**config.py**`                  | `**EngineConfig**`、`load_engine_config`（如 `/ro/config/engine.json`）                                                    |
| `**proxy.py**`                   | `**BusinessProxy**`：保留 `chat`、设备/VM、subagent 的遗留代理；不再代理 `memory`/`notebook`/`task`/`search`                                                                            |
| `**cli.py**`                     | `novaic` CLI：Cortex `/v1/*` + `/v1/proxy/*`                                                                            |
| `**auth.py**`                    | 能力 JWT 签发/校验（`CORTEX_JWT_SECRET`）                                                                                      |
| `**observability.py**`           | `log_cortex(event, **kwargs)` 结构化日志                                                                                    |


---

## 4. 存储与键空间

### 4.1 逻辑路径：`/ro` 与 `/rw`

- `**/ro/**`：Cortex 管理（scopes、config、skills、knowledge）。Agent 仅可 **读**（`read` / `list_dir` / `exists`）；**写**须走 `**Workspace._sys_*`**（服务端/内部路径）。
- `**/rw/`**：Agent 可读写（`write`、`append_line`、`delete` 等），主要为 `**scratch`** 与 sandbox 回写。

### 4.2 对象键（S3）

注册表为每个用户分配前缀 `**users/{user_id}/`**，其下 `Workspace` 再映射：

- `agents/{agent_id}/ro/...`
- `agents/{agent_id}/rw/...`

逻辑路径必须以 `/ro/` 或 `/rw/` 开头，`..` 等非法路径被拒绝。

### 4.3 Scope 目录（概念）

- 活跃根 scope：`/ro/active/{scope_id}/`
- 归档后：`/ro/scopes/{scope_id}/`，并追加到 `**/ro/scopes/_index.jsonl`**
- 子 scope 可在父 scope 的 `steps/` 下以目录形式出现；**Recall 仅对 depth==0 的根归档 scope 做记忆摘要**（见 `recall.py`）

---

## 5. 上下文引擎：时间线与 DFS

### 5.1 时间线：`steps/_index.jsonl`

`ContextEngine` 顺序读取当前 scope 下的 `**steps/_index.jsonl`**，每条描述一步，类型包括（以 engine 为准）：

- `**env`**：内联环境信息 → system 消息  
- `**assistant`**：指向 JSON 文件 → assistant（含可选 `tool_calls` / `reasoning_content`）  
- `**tool`**：指向 JSON 文件 → `role: tool` + `tool_call_id`  
- `**scope**`：子 scope 目录；若子 scope **已归档** → 折叠为一条 system（读 `summary.md`）；若仍 **开放** → **递归**子 `ContextEngine` 在子目录上 `_render_all_steps`（深度优先展开）

### 5.2 `prepare_messages_for_llm`（概要）

1. 读当前 scope 的 `**meta.json`**：可选 `system_prompt`、`recall_messages`、`initial_context`
2. 读 `**steps/_index.jsonl`**，按类型渲染
3. 调用 `**budget_compact`**（`context_stack/budget.py`）：按 `EngineConfig` 的窗口与阈值做紧急/温和压缩、长 tool 结果截断等

### 5.3 `StepTreeBuilder`（`step_tree.py`）

从索引构建 **树**（`tool` 叶 / `scope` 节点），用于分析与折叠辅助；**面向 LLM 的最终消息列表以 `engine.py` 时间线渲染为准**。

---

## 6. Recall 与 Summary 边界

- **Recall**：扫描 `**/ro/scopes/_index.jsonl`** 中 **depth==0** 的根；按 **token budget** 优先装入**较新**根 scope 的 `summary.md`，再按时间顺序输出 **system** 消息，带 `_metadata`（`origin: recall` 等）。  
- **Summary 写入边界**：自动摘要与 Gem Fusion 已退役。结构性 `scope_end` 只归档；唯一 durable summary 写入路径是 LLM 显式开启的 child skill 通过 `skill_end(report=...)` 关闭。

---

## 7. Sandbox 与 Shell

- `**Sandbox.exec()`**（`sandbox.py`）：一次调用一次临时目录：`list_recursive` 物化 `ro`/`rw` → `asyncio.create_subprocess_shell` → 仅把 `**/rw`** 上的变更写回 `Workspace`；`**/ro` 在沙箱内只读**。  
- `**Cortex.tool_shell`**（`runtime.py`）：超时来自 `**EngineConfig`**（`sandbox_timeout_default` / `sandbox_timeout_max`），并更新 metrics。  
- **与 VM 的区别**：CLI `**/v1/proxy/shell_exec`** 经 `**BusinessProxy`** 转到 Business/Device 的 **VM shell**，**不是** `sandbox.py` 这条本地文件系统 shell。

---

## 8. `Cortex` 运行时（`runtime.py`）

- 聚合 `**Workspace`、`Sandbox`、hooks、metrics。  
- `**prepare_system_prompt`**：调用 `**recall.generate()`**（注意：仓库内 **无** 名为 `prepare_llm_context` 的 Python 方法；该名称出现在 **Agent Runtime 的 topic** 中）。  
- `**skill_begin(scope_id, child_scope_id, name, ...)` / `skill_end(scope_id, child_scope_id, report)`**：创建/结束 skill scope。`**child_scope_id`** 由 LLM 显式指定，**全局唯一**（跨 active + archived）；`**skill_end`** 严格 LIFO，只能关栈顶，并将 `report` 原样写成该 child scope 的 `summary.md`。详见 [cortex/scope-lifecycle.md §9](cortex/scope-lifecycle.md#9-skill-scope-生命周期llm-可见栈式)。  
- 内置工具 schema 与 `load_tool_schemas`、技能安装 `install_skill` 等与 `**tool_schemas.py**`、`**/ro/skills**` 联动。

---

## 9. HTTP API 分层（`api.py`）

所有业务路由集中在 `**api.py**`，版本前缀多为 `**/v1/**`（健康检查除外）。

### 9.1 健康与认证

- `**GET /health**` → `{"status":"ok","service":"cortex"}`  
- 多数 Agent/CLI 路由使用 `**Authorization: Bearer**` + `**auth.verify_capability_token**`（`auth.py`）。  
- `**POST /v1/token**`：签发能力 JWT（body 含 `user_id`、`agent_id`、`scope_id`、可选 `permissions`、`ttl`），**不**要求已有 Bearer（内部调用场景）。

### 9.2 对外能力（节选）

- **Shell / Skill**：`POST /v1/shell`，`POST /v1/skill/begin`，`POST /v1/skill/end`  
- **CLI 风格**：`GET /v1/read`，`POST /v1/write`，`GET /v1/ls`，`GET /v1/recall`，`GET /v1/tools`，`POST /v1/proxy/{command}`  
- **内部 Worker 风格（tenant 在 JSON body）**：  
  - `**/v1/scope/*`**：创建/结束/激活 scope 等  
  - `**/v1/context/*`**：`**context_prepare_for_llm`**（对应 Agent Runtime 侧「组装 LLM 消息」）、`context_skill_begin/end`、`context_status`  
  - `**/v1/meta/***`：会话 `meta.json`  
  - `**/v1/steps/***`：读写步骤、索引、预览  
  - `**/v1/internal/***`：内部 recall、shell、skill 等变体

完整列表以 `**api.py` 中 `@app.get/post` 注册为准**。

---

## 10. BusinessProxy 与 CLI

- `**BusinessProxy`**（`proxy.py`）：HTTP 客户端访问 `**BUSINESS_INTERNAL_URL`**，带 `**X-Internal-Key**`、`X-User-Id`、`X-Agent-Id`，**不**转发能力 JWT。  
- `**cli.py`**：环境变量 `**NOVAIC_API`**（默认 `http://localhost:19996`）、`**NOVAIC_TOKEN**`（能力 JWT）；认知命令直打 Cortex，保留的 `chat`、设备/VM、subagent 命令走 `**POST /v1/proxy/{command}**`。`memory`、`notebook`、`task`、`search` 已删除。

---

## 11. 与 Agent Runtime 的衔接

- Agent Runtime 注册 topic `**cortex.prepare_llm_context**`（见 `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`），内部 HTTP 调用 Cortex 的 `**/v1/context/...**` 与 `**context_prepare_for_llm**`，将返回的 **messages + tools** 交给 `**llm_handlers`**。  
- 因此：**「prepare_llm_context」是跨服务约定名称**；Cortex 仓库内对应实现为 `**context_prepare_for_llm` HTTP 端点 + `ContextEngine`**，而非 `runtime.py` 里同名方法。  
- **`handle_cortex_prepare_llm_context`** 会在消息末尾注入一条瞬态 **`[Active skill stack (LIFO ...)]`** system 消息（来自 `ContextEngine.status().frames`），让 LLM 看到**每层 scope_id**，`skill_end` 时才有得填。  
- **Subagent 休息**已与「没有 tool_calls」解耦：**`react_actions`** saga 新增 **`check_skill_stack`** → **`CORTEX_CHECK_STACK`**，栈空才走 `subagent_rest`，非空继续下一轮 `react_think`。**`subagent_rest` 工具已删除**。  
  `_decide_rest_or_continue` 依次判：**（a）** `round_num ≥ services.json runtime.max_rounds_before_force_rest`（默认 40）→ 强制 rest；**（b）** Cortex 查栈异常（`stack_known=False`）→ fail-safe 继续 think，不 rest；**（c）** `stack_depth == 0` → rest；否则继续 think。  
- **`skill_begin` / `skill_end` 并发安全**：Cortex API 在 `/v1/context/skill_begin` 与 `/v1/context/skill_end` 两个端点使用**按 `(user_id, agent_id, root_scope_id)` 的 asyncio 互斥锁**（`_SKILL_LOCKS`），同一 root scope 内的技能生命周期操作全串行，避免 `resolve_active_scope_path` 并发竞态。锁条目在 `/v1/scope/end`（root）归档后通过 `_drop_skill_lock` 自动回收。  
- **Meta skill**：`subagent_wake` saga 在 `session_init` 后**必需**执行 **`CORTEX_SKILL_BEGIN`**（`child_scope_id = meta-<root>`、`name = meta`，**不再是 optional**），保证唤醒后栈非空；同时 `/api/queue/dispatch` 要求 `user_id` 必填（为 Meta skill 提供 tenant 上下文）。  
- **归档时的子 scope 收尾**：`Workspace.archive_root_scope` 在 move 到 `/ro/scopes/` 前会调用 `_auto_close_open_children` DFS 关闭所有仍 open 的子 scope（summary = `"[auto-closed on rest: scope left open by agent]"`），保证 archive 后 `phase` 全部一致。  
- **逐步调用链（Saga → Bridge → HTTP → `budget_compact`）** 见专题 **[cortex/agent-runtime-cortex-call-chain.md](cortex/agent-runtime-cortex-call-chain.md)** 与 **[cortex/agent-runtime-all-topics.md](cortex/agent-runtime-all-topics.md)**。

---

## 12. 可观测性与测试

- `**log_cortex(event, **kwargs)`**：统一前缀 `[CORTEX]`，值长度截断。  
- 各模块广泛使用 `**logging.getLogger(__name__)`**。  
- 测试位于 `**novaic-cortex/tests/`**（扁平目录），如 `test_workspace*.py`、`test_sandbox*.py`、`test_recall*.py`、`test_context_budget*.py`、`test_engine_*.py` 等；`**ContextEngine` 多通过 API 与 budget/配置间接覆盖**。

---

## 13. 配置

- `**EngineConfig`**（`config.py`）：`context_window`、compact 阈值、tool 输出上限、sandbox 超时等，常由 `**/ro/config/engine.json`** 经 `load_engine_config` 加载。  
- 与父目录文档 `**docs/architecture/cortex.md**` 的部署表一致处：端口 **19996**、OSS 环境变量；**以子模块 `README` 与 `config.py` 为最新准**。

---

## 14. 相关链接


| 文档                                                               | 说明                                      |
| ---------------------------------------------------------------- | --------------------------------------- |
| [architecture/cortex.md](architecture/cortex.md)                 | 父仓纲要（HANDOVER 对齐）                       |
| [architecture/agent-pipeline.md](architecture/agent-pipeline.md) | Agent Runtime ↔ CortexBridge            |
| [historical-doc-links.md](historical-doc-links.md)               | 删除前的长文 `cortex-architecture.md`（git 历史） |
