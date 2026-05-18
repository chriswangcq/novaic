# Sandbox 与 Shell 执行

> 源码：`novaic_cortex/sandbox.py`（`Sandbox`）、`runtime.py`（`Cortex.tool_shell`）、`api.py`（`POST /v1/shell`、`/v1/internal/shell`）。

## 1. 模型：一次 `exec` = 一次生命周期

模块头注释写清楚：**无跨 exec 缓存、无连接池、无残留状态**。

1. 新建**临时目录**
2. `list_recursive` 把当前 agent 的 `/ro/`、`/rw/` 从 store **物化**到临时盘（跳过空 `.keep`）
3. 设置环境变量：`RO`、`RW`、`CORTEX_RO`、`CORTEX_RW`、`HOME=$RW`、`NOVAIC_API`（默认 `http://localhost:19996`）；若构造时传入 `token_factory`，则还有 `NOVAIC_TOKEN`（能力 JWT）
4. `asyncio.create_subprocess_shell`，`cwd` 默认在 `rw` 下（受 `_resolve_cwd_under_rw` 约束，不能逃出 `rw`）
5. `asyncio.wait_for(..., timeout)`；超时则 kill，**exit_code = -1**
6. 对比执行前后 `/rw` 下文件的 `(mtime_ns, size)`，**仅把变更写回** `Workspace`（`write_bytes` / `delete`）
7. 删除临时目录

返回 `ShellResult`：`stdout`、`stderr`、`exit_code`、`files_changed`（逻辑路径 `/rw/...`）。

### 稳定文件视图

Sandbox 内部每次仍然使用新的临时 backing 目录，但 agent 可见的 Cortex 文件路径是稳定的：

- `/cortex/ro`：只读 Cortex workspace 视图，对应当前 agent 的 `/ro/`
- `/cortex/rw`：可写 workspace 视图，对应当前 agent 的 `/rw/`
- `$RO` / `$RW` 和 `$CORTEX_RO` / `$CORTEX_RW` 仍可用；shell 输出会把真实临时路径脱敏成 `/cortex/ro` / `/cortex/rw`

agent 可以把一次 shell 输出里的 `/cortex/ro/...` 路径复制到下一次 shell 调用继续 `cat` / `sed` / `find`。相反，`novaic-cortex-sandbox-*` 是内部临时 backing 路径，不属于稳定契约；shell 命令中出现这类路径会被拒绝并提示使用稳定路径。

---

## 2. 与 `EngineConfig` 的关系

- `Cortex.tool_shell`（`runtime.py`）用 `sandbox_timeout_default`，且不超过 `sandbox_timeout_max`。
- `Sandbox` 构造：`initialize()` 后用 `cfg.sandbox_timeout_max` 作为 `max_wall_timeout`，单次 `exec` 内 `timeout = min(请求, max_wall_timeout)`。

---

## 3. 可选保护：`max_sync_bytes`

若设置，物化前 `_estimate_sync_bytes` 超过阈值则 **拒绝执行**（防一次拉取过大）。

---

## 4. 与设备/VM 工具的区别

- **本 Sandbox**：子进程在 **Cortex 机**上跑，看到的是 **物化后的 workspace 文件**。
- **设备/VM 工具**：由 Agent Runtime tool executor 调用 Business/Device 路径执行，**不是** Cortex CLI 或 `sandbox.py` 的职责。
- Cortex 不再提供 `BusinessProxy` 或 `/v1/proxy/{command}`。

---

## 相关

- [object-keys.md](object-keys.md)
