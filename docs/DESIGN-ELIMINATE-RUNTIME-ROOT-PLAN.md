# 设计方案：从根源消灭 Gateway、Tools Server 的 Runtime 逻辑

> 本文档为 Phase 1/2 完成后的**根因级清理方案**，目标是在 Gateway 和 Tools Server 中彻底消除 runtime 概念与命名。

---

## 一、目标与原则

### 1.1 目标

1. **Gateway**：无 runtime 业务逻辑、无 runtime 表、无 runtime 命名（除必须透传 RO 的字段）
2. **Tools Server**：无 runtime 命名，统一为 subagent / tool-context 维度
3. **原则**：RO 内部保留 runtime_id；Gateway、Tools Server 对外仅使用 agent_id + subagent_id

### 1.2 边界（不改动）

| 项目 | 说明 |
|------|------|
| **Runtime Orchestrator 服务名** | RO 为独立服务，改名超出本文范围 |
| **RUNTIME_ORCHESTRATOR_URL** | Gateway 需调用 RO，保留 |
| **shared_runtime_common** | 共享包，RuntimeStatus/RuntimePhase 等由 RO 使用 |
| **HRL 中的 runtime_id** | 由 RO 写入，Gateway 仅存储；若根除需 RO 改 schema，见 Phase 4 |

---

## 二、当前状态（Phase 1/2 已完成）

### 2.1 已消除

| 项目 | 状态 |
|------|------|
| Gateway: resolve_runtime_ids, get_runtime_context, _runtime_to_dict | ✅ 已删 |
| Gateway: maybe_forward, RuntimeRepository, runtime.py | ✅ 已删 |
| Gateway: message/subagent 中 maybe_forward 调用 | ✅ 已删 |
| Tools Server: RuntimeManager, RuntimeContext, runtime_manager.py | ✅ 已改为 ToolContextManager, SubAgentToolContext |
| Tools Server: 内部 key 从 runtime_id 改为 context_key | ✅ 已完成 |

### 2.2 仍残留（待清理）

**Gateway：**

| 类别 | 位置 | 说明 |
|------|------|------|
| 表结构 | schema.py | agent_runtimes 表（v40 已清空，未 DROP） |
| 表结构 | schema.py | pipeline_tasks.runtime_id 列 |
| 数据 | subagents.hrl | 存储 runtime_id 列表（RO 写入） |
| 注释 | __init__.py, fix_indexes.sql 等 | 多处 RuntimeRepository、agent_runtimes 注释 |
| 接口 | subagent HRL API | add_to_hrl(runtime_id), remove_runtime_ids |

**Tools Server：**

| 类别 | 位置 | 说明 |
|------|------|------|
| 兼容参数 | executor.py | runtime_id, runtime 参数；self.runtime_id 别名 |
| 配置 | services.json, policy | max_concurrent_tools_per_runtime |
| 日志 | main_tools.py | "runtime(s)" 文案 |
| 响应 | session_state | "runtime" 字段 |
| 注释 | api.py, executor.py | "Runtime 管理"、"Legacy runtime_id routes" |

---

## 三、Phase 3：Gateway 根除 Runtime

### 3.1 DROP agent_runtimes 表

| 文件 | 改动 |
|------|------|
| **schema.py** | 新增 v43 迁移：`DROP TABLE IF EXISTS agent_runtimes` |
| **fix_indexes.sql** | 删除 agent_runtimes 相关索引语句与注释 |

**前置条件**：确认无代码引用 agent_runtimes（Phase 1 已删 RuntimeRepository）。

### 3.2 pipeline_tasks.runtime_id 处理

**现状**：pipeline_tasks 用于三任务架构，runtime_id 关联执行上下文。

**选项**：

| 选项 | 说明 |
|------|------|
| **A. 保留** | 若 pipeline_tasks 仍被 Gateway 使用，且任务与 RO runtime 强绑定，保留 runtime_id 作为外键语义（仅存储，不解析） |
| **B. 迁移为 context_key** | 新增 context_key 列，迁移数据，弃用 runtime_id。需确认 pipeline_tasks 的写入方 |

**建议**：先 grep 确认 pipeline_tasks 的读写方。若仅为 RO 或已废弃，可考虑移除；否则保留并加注释「仅存储 RO 的 runtime_id，Gateway 不解析」。

### 3.3 注释与文档清理

| 文件 | 改动 |
|------|------|
| **gateway/db/repositories/__init__.py** | 删除 "v12: Added RuntimeRepository" 等过时注释 |
| **gateway/db/fix_indexes.sql** | 删除 agent_runtimes、RuntimeRepository 相关注释 |
| **gateway/db/schema.py** | 版本注释中标注 v43 删除 agent_runtimes |

### 3.4 HRL 与 runtime_id（可选，需 RO 配合）

**现状**：subagents.hrl 存 `["rt-xxx", "rt-yyy"]`，由 RO 通过 `/hrl/add` 写入。

**根除路径**：

1. RO 改为传 `context_key`（如 `agent_id:subagent_id`）或内部生成不暴露 runtime_id 的标识
2. Gateway HRL 存储新标识，接口参数改为 `context_key` 或 `identifier`
3. 需 RO 与 Gateway 同步发版

**建议**：Phase 3 不修改 HRL。HRL 中的 runtime_id 视为「RO 的 opaque 标识」，Gateway 不赋予业务含义，仅作存储。若后续 RO 改 schema，再单独做 Phase 4。

---

## 四、Phase 4：Tools Server 根除 Runtime 命名

### 4.1 移除 Executor 兼容参数

| 文件 | 改动 |
|------|------|
| **executor.py** | 删除 `runtime_id`、`runtime` 参数；仅保留 `context_key`、`context` |
| **executor.py** | 删除 `self.runtime_id = self.context_key`，所有引用改为 `self.context_key` |
| **调用方** | 确认无代码传入 runtime_id/runtime（api.py 已用 context） |

### 4.2 配置与策略重命名

| 原命名 | 新命名 | 位置 |
|--------|--------|------|
| max_concurrent_tools_per_runtime | max_concurrent_tools_per_context | services.json, policy, tests |
| max_concurrent_per_runtime | max_concurrent_per_context | config |

### 4.3 日志与响应

| 文件 | 改动 |
|------|------|
| **main_tools.py** | "runtime(s)" → "context(s)" |
| **executor.py** | 日志中的 "runtime" → "context" |
| **session_state** | "runtime" 字段 → "tool_context"（或保留兼容，加 "tool_context" 新字段） |

### 4.4 注释与文档

| 文件 | 改动 |
|------|------|
| **api.py** | "Runtime 管理" → "Tool context 管理" |
| **api.py** | "Legacy runtime_id routes" → "Legacy context_key routes" 或删除 |
| **executor.py** | 旧路由注释中的 runtime_id → context_key |

### 4.5 测试修复

| 文件 | 改动 |
|------|------|
| **test_api_reliability_controls.py** | 若 call_tool 不存在，改为测试 call_subagent_tool 或移除/跳过 |
| **test_reliability_policy.py** | 移除 reliability_policy 参数（若 ToolExecutor 不支持）或补齐 reliability 模块 |
| **test 中的 runtime 命名** | SimpleNamespace(runtime_id=...) → context_key=... |

---

## 五、Phase 5：Gateway HRL 去 runtime_id（可选，需 RO 协同）

### 5.1 目标

HRL 不再存储 runtime_id，改为存储 RO 的 context 标识或移除 HRL 的 runtime 语义。

### 5.2 前置条件

- RO 已支持用 context_key 或等效标识管理 HRL
- RO 的 merge-history、hrl/add 等接口已改为传 context_key

### 5.3 改动

| 组件 | 改动 |
|------|------|
| **Gateway subagent API** | /hrl/add 参数 runtime_id → context_key |
| **Gateway SubAgentRepository** | add_to_hrl(..., context_key), remove_from_hrl(..., context_keys) |
| **subagents.hrl** | 存储 context_key 列表（或 RO 定义的新标识） |
| **RO** | 同步修改 HRL 写入逻辑 |

---

## 六、施工顺序与依赖

```
Phase 3 (Gateway)              Phase 4 (Tools Server)
DROP agent_runtimes            移除 executor 兼容参数
清理注释/文档                  重命名配置、日志、响应
pipeline_tasks 评估            修复测试
```

| 阶段 | 任务 | 预估 | 依赖 |
|------|------|------|------|
| Phase 3 | Gateway DROP agent_runtimes、清理注释 | 0.5d | 无 |
| Phase 4 | Tools Server 移除 runtime 命名、修复测试 | 0.5d | 无 |
| Phase 5 | HRL 去 runtime_id（可选） | 1d | RO 配合 |

---

## 七、验收标准

### Gateway

1. 无 agent_runtimes 表（或已 DROP）
2. 无 RuntimeRepository、resolve_runtime_ids、get_runtime_context、maybe_forward
3. 注释与文档无过时 runtime 引用（除 HRL、pipeline_tasks 的合理说明）

### Tools Server

1. 无 RuntimeManager、RuntimeContext、runtime_manager
2. 无 runtime_id 作为主键或参数（除兼容层）
3. 配置、日志、响应统一为 context / tool_context 命名

### 端到端

1. 工具注册、调用、恢复流程正常
2. RO → Tools Server、RO → Gateway 调用正常

---

## 八、风险与回滚

| 风险 | 缓解 |
|------|------|
| DROP agent_runtimes 影响已有部署 | v43 迁移前确认无写入；保留迁移脚本可回滚 |
| 移除 executor 兼容参数导致调用方报错 | grep 确认无 runtime_id/runtime 调用方 |
| 配置重命名导致服务启动失败 | 保留旧 key 的 fallback 读取，或同步更新所有配置 |

---

## 九、相关文档

- [DESIGN-ELIMINATE-RUNTIME-FROM-GATEWAY-TOOLS-SERVER.md](./DESIGN-ELIMINATE-RUNTIME-FROM-GATEWAY-TOOLS-SERVER.md)（原设计，Phase 1/2 已执行）
- [INVESTIGATION-GATEWAY-RUNTIME-USAGE.md](./INVESTIGATION-GATEWAY-RUNTIME-USAGE.md)
