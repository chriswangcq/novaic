# 8-way parallel implementation plan

| # | Owner | Primary files | Depends on |
|---|--------|---------------|------------|
| 1 | Lead | `store.py`, `types.py`, `protocols.py`, `workspace.py`, `pyproject.toml`, `CONTRACTS.md` | — |
| 2 | Subagent | `sandbox.py` | workspace |
| 3 | Subagent | `compactor.py` | workspace |
| 4 | Subagent | `recall.py` | workspace |
| 5 | Subagent | `runtime.py` | 2–4 |
| 6 | Subagent | `hooks.py`, `tool_schemas.py`, `__init__.py` | runtime |
| 7 | Subagent | `tests/test_store.py`, `tests/test_workspace.py` | 1 |
| 8 | Subagent | `tests/test_sandbox.py` … `test_runtime.py` | 2–5 |

**Rule:** Subagents own only their listed files; lead owns store/workspace and integration contracts.

**Executed:** 2026-04-03 — initial commit `31de389`; `pytest` 12 passed.

## Wave 2（8 人 coder 团队）

| # | Coder | 负责 | 合并后契约 |
|---|-------|------|------------|
| 1 | Coder-1 | `s3_store.py`、`pyproject.toml` `[s3]`、`S3Store` 导出 | `boto3` 可选 |
| 2 | Coder-2 | `sandbox.py` 全量 materialize / persist `rw` | `max_sync_bytes` |
| 3 | Coder-3 | `workspace.py` `hooks`、`on_scope_created`、`..` 校验 | — |
| 4 | Coder-4 | `compactor.py` `hooks`、`gem_fusion_*`、L1+L2、`on_scope_archived` / `on_fusion` | **归档钩子仅此触发** `(scope_id, summary, archive_path)` |
| 5 | Coder-5 | `runtime.py` `CortexHooks`/`CortexMetrics`、`scope_create`、tool 路径校验 | `Compactor(..., hooks=...)` 由 lead 对齐 |
| 6 | Coder-6 | `config.py`、`EngineConfig`、`load_engine_config` | — |
| 7 | Coder-7 | `test_s3_store.py`、`test_sandbox_sync.py` | moto 可选 |
| 8 | Coder-8 | `test_hooks_metrics.py`、`test_workspace_paths.py`、`PARALLEL_PLAN` 本段 | 钩子签名与 Coder-4 一致 |

**集成约定**：`on_scope_archived` **只**在 `Compactor.compact` 里 `archive_scope` 之后触发，避免与 `Workspace` 重复。

**Executed:** Wave2 合并后 `pytest`：**16 passed, 1 skipped**（无 boto3/moto 时 S3 测例 skip）。

## Wave 3（8 人 coder 团队）

| # | Coder | 负责 | 合并后契约 |
|---|-------|------|------------|
| 1 | Coder-1 | `Cortex` / runtime 启动路径调用 `load_engine_config`，将 `EngineConfig` 注入 `Recall`、`Compactor`、`Sandbox` 超时默认值 | 单一配置源：`/ro/config/engine.json` |
| 2 | Coder-2 | `recall.py`：token / 字符预算与 `EngineConfig.fuzzy_memory_token_budget`、`micro_*` 对齐；`generate()` 行为与设计 §Recall 一致 | 无硬编码预算 |
| 3 | Coder-3 | `workspace.py`：`initialize` 与 config 联动（如需要时确保 `engine.json` 可读路径）；路径与安全校验与 Wave2 钩子契约兼容 | — |
| 4 | Coder-4 | `compactor.py`：`gem_fusion_*`、`compact_threshold` 等仅从 `EngineConfig`（或显式参数覆盖）读取 | 与 Coder-1 注入方式一致 |
| 5 | Coder-5 | `runtime.py` / `tool_schemas.py`：工具 JSON schema 与运行时参数、路径规则一致；可选 stricter 校验 | 与 `CONTRACTS.md` 对齐 |
| 6 | Coder-6 | `observability.py`：`log_cortex` 覆盖关键路径缺口；`CortexMetrics` 序列化或导出（如 `asdict`/调试 API）供宿主集成 | 不破坏现有事件名 |
| 7 | Coder-7 | 新增或扩展 E2E 测例：建 scope → read/write → `scope_end`/compact → `Recall.generate` 含预期片段 | `pytest` 全绿 |
| 8 | Coder-8 | 更新 `CONTRACTS.md`、本文件 Wave3 执行摘要；设计与代码交叉引用 | 与 Coder-4/5 签名一致 |

**集成约定**：配置在 runtime 层加载一次并向下传递；子模块禁止各自再读 `engine.json` 除非 lead 明确拆分（避免竞态与默认值漂移）。

**Lead 合并补丁**：去掉 `Workspace.archive_scope` 内重复的 `scope.archived` 日志（保留 `Compactor` 中带 `summary_len` 的一条）；`initialize()` 后重建 `Sandbox(max_wall_timeout=cfg.sandbox_timeout_max)`。

**Executed:** Wave3 合并后 `pytest`：**20 passed, 1 skipped**；新增 `observability.py`、`test_engine_wiring.py`、`test_tool_metrics.py`、`test_compaction_meta.py`；`README.md` 补全 Features / Config / Observability。

## Wave 4（8 人 coder 团队）

| # | Coder | 负责 | 合并后契约 |
|---|-------|------|------------|
| 1 | Coder-1 | `CONTRACTS.md` 与 Wave3 实现对齐（含 S3、hooks、metrics、log 事件） | 单一事实源 |
| 2 | Coder-2 | `types.py`：`skills_installed` / `compactions_completed`、`metrics_as_dict` | `__init__.py` 导出 |
| 3 | Coder-3 | `compactor.py`：`summarizer_max_tokens`、`total_tokens_saved`、`summary_chars` | `Summarizer.summarize(..., max_tokens=)` |
| 4 | Coder-4 | `runtime.py`：`auto_summary_max_tokens` → Compactor；skill/compaction 计数 | 与 Coder-2 字段一致 |
| 5 | Coder-5 | `tool_schemas.py` + `README`：`engine.json` 交叉引用、`auto_summary_max_tokens` 说明 | — |
| 6 | Coder-6 | `store.py`：并发/线程安全说明（Memory/Local/S3） | — |
| 7 | Coder-7 | `tests/test_localfilestore.py`：嵌套路径、`list_recursive`、`move_prefix` | LocalFileStore 语义 |
| 8 | Coder-8 | `tests/test_wave4_metrics.py`；本段 Wave4 表（已由 lead 校正） | — |

**集成约定**：`scope_end` 成功后递增 `compactions_completed`；`total_tokens_saved` 仅在 `estimate_tokens(messages) - estimate_tokens(summary) > 0` 时累加。

**Lead 补丁**：`CONTRACTS.md` §CortexMetrics 补全 Wave4 新增字段与 `metrics_as_dict`。

**Executed:** Wave4 合并后 `pytest`：**24 passed, 1 skipped**。

## Wave 5（8 人 coder 团队）

| # | Coder | 负责 | 合并后契约 |
|---|-------|------|------------|
| 1 | Coder-1 | `tests/test_s3_store_integration.py`：`S3Store` + moto（put/get/list/move、`list_objects`） | 无 boto3/moto 时 class skip |
| 2 | Coder-2 | `recall.py`：可选 `TokenCounter`、`_tokens` / `_truncate_section` | 未注入 ≡ `estimate_tokens` |
| 3 | Coder-3 | `runtime.py`：`token_counter` → `Recall`；`initialize` 一致 | — |
| 4 | Coder-4 | `context_budget.py`：`usage_ratio`、`compact_level`（`normal` / `emergency` / `none`） | `__init__.py` 导出 |
| 5 | Coder-5 | `runtime.py`：`async suggest_compact(used_tokens)` | 仅用缓存 `config` 或默认 `EngineConfig` |
| 6 | Coder-6 | `test_tool_schemas_shape.py`、`test_context_budget.py` | — |
| 7 | Coder-7 | `test_recall_token_counter.py`、`test_suggest_compact.py` | — |
| 8 | Coder-8 | `CONTRACTS.md`、`README.md`、Wave5 表初稿 | — |

**集成约定**：宿主持有「已用 token」；`context_budget` / `suggest_compact` 只读数值与 `EngineConfig`，不访问 store。`TokenCounter` 可选传入 `Cortex` → `Recall`。

**Lead 补丁**：`runtime.py` 直接 `from novaic_cortex.context_budget import ...`，去掉与 `compact_level` 返回值不一致的 fallback（统一为 `"normal"`）。

**Executed:** Wave5 合并后 `pytest`：**32 passed, 2 skipped**（S3 集成 + 原 S3 用例在无 boto3/moto 时 skip）。

## Stress QA sweep（8 人并行极限测试）

| # | 范围 | 主要交付 |
|---|------|----------|
| 1 | Store | `test_store_limits.py`（二进制/大对象/Unicode/并发 put/`list_objects` 边界） |
| 2 | S3 | `test_s3_store_limits.py`（moto 下 overwrite、空桶、delimiter、`move`/`move_prefix`、长 key） |
| 3 | Context budget | `test_context_budget_limits.py`、`test_context_budget_stress.py`；`usage_ratio` 极大整数防 `OverflowError` |
| 4 | Recall | `test_recall_limits.py`；`test_recall_stress.py`（若存在） |
| 5 | Sandbox / Compactor | `test_sandbox_limits.py`、`test_compactor_limits.py`、`test_sandbox_stress.py`（`log_cortex` patch 指向 `observability`） |
| 6 | 路径滥用 | `test_runtime_path_abuse.py`、`test_paths_adversarial.py` |
| 7 | Engine 配置 | `test_engine_config_limits.py` |
| 8 | 集成 | `test_cortex_chaos.py` |

**Lead 补丁**：`workspace._key` 在校验前折叠 `//` → `/`，与 adversarial 契约一致，避免 `tool_write("/rw//a")` 与 `tool_read("/rw/a")` 指向不同对象。

**Executed:** 全量 `pytest`：**176 passed, 13 skipped**（S3/moto 等按环境 skip）。

## Stress QA sweep — round 2（再派 8 人）

| # | 范围 | 主要交付 |
|---|------|----------|
| 1 | Gem fusion / 多 scope | `test_fusion_limits.py`（小 merge_factor、重复 scope_id、`gem_fusion_enabled`、`max_level` L1/L2） |
| 2 | Hooks / metrics | `test_hooks_limits.py`（同步/异步 hook 抛错 → `UserWarning` 且操作完成；链式 hook；metrics 不意外清零） |
| 3 | `install_skill` | `test_skill_install_limits.py`（空名、Unicode、重复安装对 metrics/index 的语义） |
| 4 | Tool schemas | `test_tool_schemas_limits.py`（工具名冻结集合、描述/属性数量上限、顶层键最小集） |
| 5 | LocalFileStore | `test_localfilestore_limits.py`（长文件名、`delete` 幂等、symlink/越界按当前实现断言） |
| 6 | 归档不变式 | `test_archive_invariants.py`（`meta.json` 键、`summary.md` 换行/Unicode、`../`/NUL scope_id 拒绝） |
| 7 | Engine 配置往返 | `test_engine_config_roundtrip.py`（默认与全字段 JSON 往返、极端 int、float） |
| 8 | Workspace | `test_workspace_limits.py`（缺失路径 `KeyError` vs 缺失 scope `FileNotFoundError`、`list_dir` 尾部 `/` 与 `//`） |

**Executed (round 2 合并后):** 全量 `pytest`：**219 passed, 13 skipped**。

## Design–implementation gap closure（设计对照补齐）

对照 `docs/cortex-design-implementation-gaps.md`：**实现与文档由 lead 合并落地**（避免多人同时改 `compactor.py` / `runtime.py` 冲突）。覆盖：通用 gem fusion（L1…`gem_fusion_max_level`）+ 批次去重、JSONL → `tools_used` / `files_changed`、`Sandbox.files_changed` 含删除、`Recall` 纳入 `constraints.md`、`tool_read`/`tool_shell` 接线 engine 字段、`install_skill` 深度与 hook、`create_scope` 工具 schema + `scratch/.keep`、日志字段、设计 §5/§6/§11/§12/§4.3–4.6/§8、`CONTRACTS.md` 与 gap 文档闭合表。

**Executed:** 全量 `pytest`：**224 passed, 13 skipped**。

---

# 存储统一 + Cortex 集成（阶段 1-4）

> 设计文档：`docs/oss-storage-unified-plan.md`  
> 前置已完成：`steps/` 基础（`write_step` / `list_steps`、263 tests passed）
>
> **阶段 1 进度：** Task 1 (TenantLayout) 完成 → `novaic_cortex/tenant.py` + `tests/test_tenant.py`（27 新增测试）；全量 290 passed。

## 现有架构速查

```
LLM ←→ agent-runtime (react_think / react_actions)
                ↓ POST /tools/call
          Tools Server → Cortex steps/ → step_id
                ↓ append_context(tool_result, step_id)
          Cortex Workspace → context 持久化
                ↓ next turn: expand via Cortex step read
          agent-runtime → LLM
```

**关键发现：**
- Gateway **不**直接使用 Cortex（只代理 TRS / File Service）
- agent-runtime 的 `react_actions` 是 tool 执行编排入口
- `result_id` 模式：TRS 存全量，runtime context 只存引用
- Cortex scope 目前只在 `novaic-cortex` 包内，未接入任何宿主

## 阶段 1：Cortex Workspace 接入 agent-runtime（6 人）

**目标：** agent 每个 runtime session 对应一个 Cortex scope；tool 结果写入 `steps/`。

| # | Coder | 负责文件 | 具体任务 | 验收 |
|---|-------|----------|---------|------|
| 1 | Coder-1 | 共享库（新包或 `novaic-cortex` 导出） | 实现 `TenantLayout` dataclass（`user_id` → `store_prefix` / `attachments_prefix`）；`user_id` 校验（同 `agent_id` 规则：无 `/`、`..`、NUL） | 单元测试 |
| 2 | Coder-2 | `novaic-agent-runtime/task_queue/sagas/runtime_start.py` | `RUNTIME_CREATE` 后增加 step：构建 `S3Store(prefix=TenantLayout.store_prefix)` + `Workspace` + `create_scope`；scope_id = runtime_id；store 实例缓存到 saga context | runtime_start 后 OSS 可见 `users/{uid}/agents/{aid}/rw/active/{rid}/steps/.keep` |
| 3 | Coder-3 | `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` | `handle_tool_execute` 成功后追加 `write_step(scope_id, {type: "tool", call_id, tool, status, result, duration_ms})` | tool 执行后 `list_steps` 返回该 step 文件 |
| 4 | Coder-4 | `novaic-agent-runtime/task_queue/sagas/react_actions.py` | `_build_save_results_tasks` 中：除现有 TRS 写入外，并行调 `write_step`；大 artifact 仍走 TRS/File Service，step JSON 存引用 | `steps/` 与 TRS 双写；result_id 和 step seq 均可查 |
| 5 | Coder-5 | `novaic-agent-runtime/task_queue/sagas/react_actions.py` | `runtime_complete` 触发时：调 Cortex `scope_end(scope_id, report=最后一轮 summary)`；scope 归档 + optional gem fusion | 归档后 `ro/scopes/{rid}/steps/` 可读 |
| 6 | Coder-6 | 测试 + 配置 | E2E 测试：`runtime_start` → tool_execute × 3 → `runtime_complete`；验证 `list_steps` 时序、归档后可读；环境变量 `NOVAIC_OSS_*` 文档 | pytest 全绿 |

**集成约定：**
- `user_id` 从 Gateway JWT `sub` 传入（已有 `get_current_user`），经 runtime context 透传到 agent-runtime
- Cortex Workspace 实例生命周期 = runtime session（不跨 session 复用）
- `write_step` 与 TRS 双写期间保持兼容；TRS 不删，后续阶段退化

## 阶段 2：storage-b (TRS) 退化（4 人）

**目标：** tool 结果主路径从 TRS → Cortex steps/；TRS 降为可选 fallback。

| # | Coder | 负责文件 | 具体任务 | 验收 |
|---|-------|----------|---------|------|
| 1 | Coder-1 | `novaic-agent-runtime/task_queue/utils/trs_client.py`、`trs_sdk.py` | `expand_messages_for_llm` 优先从 Cortex `read(/ro/scopes/{sid}/steps/{call_id}.json)` 读取 result；TRS 作为 fallback | 停掉 TRS 后 LLM 仍能拿到 tool 结果 |
| 2 | Coder-2 | `novaic-agent-runtime/task_queue/sagas/react_actions.py` | `_build_save_results_tasks` 中移除 TRS 写入（改为 feature flag 控制）；`write_step` 成为唯一主路径 | flag=off 时纯 Cortex；flag=on 时双写 |
| 3 | Coder-3 | `novaic-gateway/main_gateway.py` | `proxy_trs` 路由改为：先查 Cortex（经 agent-runtime API 或直读 S3），fallback 到 TRS | Gateway TRS proxy 仍可用 |
| 4 | Coder-4 | 测试 + 文档 | 回归测试（TRS on/off 两种模式）；`CONTRACTS.md` 更新 TRS 退化说明 | 双模式 pytest 全绿 |

**集成约定：**
- Feature flag: `NOVAIC_USE_CORTEX_STEPS=true`（默认 true，降级用 false）
- `result_id` 概念逐步退出；step 内的 `call_id` + `scope_id` 替代

### 阶段 2.5：TRS 写入切断 + 迁移脚本（Phase 3 实施记录）

**已完成 (2026-04-04)：**

| 变更 | 文件 | 说明 |
|------|------|------|
| SKIP_TRS_PUSH flag | `novaic-tools-server/tools_server/api.py` | 环境变量 `SKIP_TRS_PUSH=true` 时跳过 TRS 推送 |
| raw_result 捕获 | `novaic-agent-runtime/task_queue/business/mcp.py` | `ToolExecuteResult` 新增 `raw_result` 字段，从 Tools Server response 直接捕获 |
| Cortex step 零 round-trip | `novaic-agent-runtime/task_queue/handlers/tool_handlers.py` | 用 `raw_result` + `parse_tool_result()` 直接写 step，不再调 `get_normalized` |
| TRS fallback deprecated | `novaic-agent-runtime/task_queue/utils/trs_client.py` | TRS 路径标记 deprecated，命中时输出 INFO 日志 |
| 迁移脚本 | `novaic-cortex/scripts/migrate_trs_to_cortex.py` | CLI 工具：扫描 Cortex steps，回填 TRS 中的 normalized 数据 |

**数据流变更（Phase 3 后）：**
```
Tool Execute → Tools Server
  ├─ [SKIP_TRS_PUSH=false] → TRS push (legacy, deprecated)
  └─ response includes raw_result
       ↓
agent-runtime tool_handlers.py
  ├─ parse_tool_result(raw_result) → three-element format
  └─ write_tool_step(step.result=parsed, step.artifacts=file_refs)

LLM context resolve:
  1. Cortex step.result (primary)
  2. TRS fallback (deprecated, logged)
```

## 阶段 3：File Service 上 OSS + attachments（4 人）

**目标：** `attachments/` 后端迁到 OSS；URL 契约不变。

| # | Coder | 负责文件 | 具体任务 | 验收 |
|---|-------|----------|---------|------|
| 1 | Coder-1 | `novaic-storage-a/file_service/` | 实现 `StorageBackend` 接口（`save_bytes` / `load_bytes` / `delete` / `exists`）+ `DiskBackend`（包装现有逻辑） | 现有测试不变 |
| 2 | Coder-2 | `novaic-storage-a/file_service/` | 实现 `OssS3Backend`（用 boto3，endpoint 同 Cortex）；写入根 = `TenantLayout.attachments_prefix` | moto 测试 |
| 3 | Coder-3 | `novaic-storage-a/file_service/` | `fs://` URL resolver 改为：从 URL 推导 `user_id` + 相对路径 → `StorageBackend.load_bytes`；对外 URL 不变 | 同一文件，Disk 和 OSS 双跑回归 |
| 4 | Coder-4 | `novaic-gateway/common/utils/image_storage.py` + 配置 | `_save_via_file_service` 路径加 `user_id` 前缀（从 request context）；收敛多处 `image_storage.py` 副本为单一引用 | Gateway upload → OSS 可见 `users/{uid}/attachments/...` |

**集成约定：**
- 环境变量 `NOVAIC_ATTACHMENTS_BACKEND=disk|oss`（默认 disk）
- OSS 模式下与 Cortex 共用同一 bucket + credential

## 阶段 4：治理与清理（2 人）— ✅ 已完成 (2026-04-04)

| # | 任务 | 状态 | 详情 |
|---|------|------|------|
| 1 | OSS 生命周期 + RAM 策略 | ✅ | `scripts/oss_lifecycle_setup.py`：90 天转 IA、365 天过期、scratch 7 天清理；RAM per-user 隔离模板 |
| 2 | 彻底移除 TRS | ✅ | 删除 `novaic-storage-b/`；删除 `tools_server/trs.py`；删除 `trs_sdk.py`；`trs_client.py` 改为 Cortex-only；Gateway `/api/trs/*` 返回 410 Gone |

**变更摘要：**
- `novaic-storage-b/` 整个目录已删除
- `novaic-tools-server/tools_server/trs.py` 已删除（TRS push）
- `novaic-tools-server/tools_server/api.py` 移除 `SKIP_TRS_PUSH` 逻辑
- `novaic-agent-runtime/task_queue/utils/trs_sdk.py` 已删除（TRS SDK）
- `novaic-agent-runtime/task_queue/utils/trs_client.py` 重写为纯 Cortex（无 TRS fallback）
- `novaic-agent-runtime/task_queue/sagas/react_actions.py` 移除 TRS 依赖
- `novaic-gateway/main_gateway.py` TRS proxy 路由返回 410 Gone

**附加改进（同期完成）：**
- `fs://` URI 改为 user-relative（不含 user_id）
- HTTP 下载路径改为 user-relative（user_id 从 `X-User-ID` header 获取）
- `default-user` 兜底全局移除（缺失 user_id 直接报错）
- `image_storage.py` 8 副本收敛为 1 实现 + 7 re-export

---

## 总览 Gantt

```
阶段 0  ████ steps/ 基础                     ✅ 已完成
阶段 1  ████████████████ Cortex 接入          ✅ 已完成
阶段 2  ████████████ TRS 退化                 ✅ 已完成
阶段 3  ████████████ File Service 上 OSS      ✅ 已完成
阶段 4  ████████ 治理 + 清理                  ✅ 已完成
```

全部阶段完成。存储统一迁移计划执行完毕。
