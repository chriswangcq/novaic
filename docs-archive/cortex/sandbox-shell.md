# Sandbox 与 Shell 执行

> 源码：`novaic_cortex/sandbox.py`（`Sandbox`）、`novaic_cortex/logical_fs.py`（`MountNamespaceLogicalFS`）、`api.py`（`POST /v1/shell`、`/v1/internal/shell`）。

## 1. 模型：一次 `exec` = 一次 LogicalFS 视图 + 一次 sandboxd 执行

Cortex 不在本进程里直接 `subprocess` 执行 shell，也不提供本地 fallback。Shell 执行由两个边界组成：

1. `MountNamespaceLogicalFS` 从 Cortex `Workspace` 构造本次执行需要的 RO/RW snapshot。
2. LogicalFS 生成 `/cortex/bin` 能力脚本：`agentctl`、`cortex`、`devicectl`。
3. LogicalFS 设置稳定环境变量：`RO=/cortex/ro`、`RW=/cortex/rw`、`CORTEX_RO=/cortex/ro`、`CORTEX_RW=/cortex/rw`，以及 `NOVAIC_API` / `NOVAIC_TOKEN` 等能力上下文。
4. `Sandbox` 组装 `SandboxExecSpec`，把本次 LogicalFS view 作为 mount plan 交给 sandboxd；mount point 是 `/cortex`，默认 cwd 是 `/cortex/rw`。
5. sandboxd 只负责在 mount view 中执行进程，返回 stdout、stderr、exit code 和耗时。
6. LogicalFS 观察 `/cortex/rw` 变化，把 RW patch 写回 Cortex `Workspace`，并返回逻辑路径形式的 `files_changed`。
7. Runtime 只把 shell stdout/stderr 当作 bounded terminal text 投影给 LLM；完整原始输出保存在 Cortex step payload 中，需要时通过 `cortex payload ...` 显式读取。

返回 `ShellResult`：`stdout`、`stderr`、`exit_code`、`files_changed`（逻辑路径 `/rw/...`）。

## 2. 稳定文件视图

Agent 可见的 Cortex 文件路径是稳定 mount namespace：

- `/cortex/ro`：只读 Cortex workspace 视图，对应当前 agent/session/scope 的 RO 工作集。
- `/cortex/rw`：可写 workspace 视图，对应当前 agent/subagent 的 RW 工作集。
- `$RO` / `$RW` 和 `$CORTEX_RO` / `$CORTEX_RW` 指向同一组稳定路径。

Agent 可以把一次 shell 输出里的 `/cortex/ro/...` 或 `/cortex/rw/...` 路径复制到下一次 shell 调用继续 `cat` / `sed` / `find`。相反，`novaic-cortex-sandbox-*` 是内部 backing 路径，不属于稳定契约；shell 命令中出现这类路径会在执行前被拒绝，并提示改用 `/cortex/ro`、`/cortex/rw`、`$RO` 或 `$RW`。

## 3. RW 工作集

为了避免每次 shell 启动都拉取全部历史 RW，LogicalFS 默认只挂载有明确实时语义的 RW 工作集：

- `/rw/` 根目录下的直接文件；
- `/rw/public/`；
- `/rw/system/`；
- 当前 subagent 的 `/rw/subagents/<subagent_id>/`；
- 本次执行生成的 `.novaic_env.json` 和能力脚本相关环境。

命令在 `/cortex/rw` 下新建或修改的文件会通过 RW patch 写回 Workspace。其他历史目录不会因为存在于 Workspace 中就被隐式全量挂载；需要大范围历史读取时，应走明确的 Cortex payload 或 Workspace 查询能力。

## 4. 与 `EngineConfig` 的关系

- `Cortex.tool_shell`（`runtime.py`）使用 `sandbox_timeout_default`，且不超过 `sandbox_timeout_max`。
- `Sandbox` 构造时把 `sandbox_timeout_max` 作为 `max_wall_timeout`，单次 `exec` 内 `timeout = min(请求, max_wall_timeout)`。
- 若设置 `max_sync_bytes`，LogicalFS snapshot 超过阈值会拒绝执行，避免一次 shell 启动读取过多 workspace 文件。

## 5. 与设备/VM 工具的区别

- **Cortex Sandbox**：在 sandboxd 管理的进程环境中执行，看到的是 LogicalFS 投影出的 `/cortex/ro`、`/cortex/rw` 和 `/cortex/bin`。
- **设备/VM 工具**：通过 shell 中的 `devicectl ...` 能力脚本走设备/Business 路径；它们可以返回 `tool-output.v1` artifact manifest，但不应该把图片、音频或 base64 bytes 打到 stdout。
- Cortex 不再提供 `BusinessProxy` 或 `/v1/proxy/{command}`。

## 相关

- [object-keys.md](object-keys.md)
