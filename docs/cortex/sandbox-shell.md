# Sandbox 与 Shell 执行

> 源码：`novaic_cortex/sandbox.py`（`**Sandbox**`）、`runtime.py`（`**Cortex.tool_shell**`）、`api.py`（`POST /v1/shell`、`/v1/internal/shell`）。

## 1. 模型：一次 `exec` = 一次生命周期

模块头注释写清楚：**无跨 exec 缓存、无连接池、无残留状态**。

1. 新建**临时目录**
2. `**list_recursive`** 把当前 agent 的 `**/ro/`、`/rw/**` 从 store **物化**到临时盘（跳过空 `.keep`）
3. 设置环境变量：`**RO`**、`**RW**`、`**HOME=$RW**`、`**NOVAIC_API**`（默认 `http://localhost:19996`）；若构造时传入 `**token_factory**`，则还有 `**NOVAIC_TOKEN**`（能力 JWT）
4. `**asyncio.create_subprocess_shell**`，`cwd` 默认在 `**rw**` 下（受 `**_resolve_cwd_under_rw**` 约束，不能逃出 `rw`）
5. `**asyncio.wait_for(..., timeout)**`；超时则 kill，**exit_code = -1**
6. 对比执行前后 `**/rw`** 下文件的 `(mtime_ns, size)`，**仅把变更写回** `Workspace`（`write_bytes` / `delete`）
7. 删除临时目录

返回 `**ShellResult`**：`stdout`、`stderr`、`exit_code`、`**files_changed**`（逻辑路径 `/rw/...`）。

---

## 2. 与 `EngineConfig` 的关系

- `**Cortex.tool_shell**`（`runtime.py`）用 `**sandbox_timeout_default**`，且不超过 `**sandbox_timeout_max**`。
- `**Sandbox` 构造**：`initialize()` 后用 `**cfg.sandbox_timeout_max`** 作为 `**max_wall_timeout**`，单次 `exec` 内 `**timeout = min(请求, max_wall_timeout)**`。

---

## 3. 可选保护：`max_sync_bytes`

若设置，物化前 `**_estimate_sync_bytes**` 超过阈值则 **拒绝执行**（防一次拉取过大）。

---

## 4. 与设备/VM 工具的区别

- **本 Sandbox**：子进程在 **Cortex 机**上跑，看到的是 **物化后的 workspace 文件**。
- **设备/VM 工具**：由 Agent Runtime tool executor 调用 Business/Device 路径执行，**不是** Cortex CLI 或 `sandbox.py` 的职责。
- Cortex 不再提供 `BusinessProxy` 或 `/v1/proxy/{command}`。

---

## 相关

- [object-keys.md](object-keys.md)
