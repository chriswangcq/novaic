# VMUSE 工具 Review（2026-03 更新）

## Mounted Tools（Agent 可配置的 3 类）

在 Agent Tools 页面，用户可为 agent 勾选以下 3 类工具，Gateway 会按 `mounted_tools` 做权限校验：

| 工具族 | 含义 | VMUSE 接口 | 说明 |
|--------|------|------------|------|
| **desktop** | 桌面控制 | `screenshot`, `mouse`, `keyboard` | 截图、鼠标、键盘 |
| **file** | 文件传输 | `pull`, `push` | VM↔Host 文件拉取/推送 |
| **shell** | 命令执行 | `run_command` | 执行 shell 命令 |
| **clipboard** | 剪贴板 | `clipboard_get`, `clipboard_set` | VM 剪贴板读写 |

### 本次改动

1. **file**：由 `read`/`write`/`info` 改为 `pull`/`push`
   - `pull`：VM 路径 → 内容（binary=True 时 base64）
   - `push`：内容 + VM 路径 → 写入
   - Executor 的 `file_pull`/`file_push` 已改为调用 `file/pull`、`file/push`

2. **shell**：仅保留 `run_command`，移除 `run_python`

3. **desktop**：无改动

---

## 其他 VMUSE 工具（未纳入 mounted）

以下工具由 VMUSE 提供，但**不在** `mounted_tools` 中，Gateway 不做 `mounted_tools` 校验（调用时仍需 agent 有 Linux VM binding）：

### Browser

| 接口 | 说明 |
|------|------|
| `navigate` | 打开 URL |
| `click` | 点击元素 |
| `type` | 输入文本 |
| `screenshot` | 页面截图 |
| `scroll` | 滚动 |
| `evaluate` | 执行 JS |
| `get_tabs` | 获取标签页 |
| `switch_tab` | 切换标签 |
| `close_tab` | 关闭标签 |

### Window

| 接口 | 说明 |
|------|------|
| `list` | 列出窗口 |
| `focus` | 聚焦窗口 |
| `maximize` / `minimize` / `close` / `resize` | 窗口操作 |
| `launch_app` | 启动应用 |

### Context（clipboard 已纳入 mounted）

| 接口 | 说明 |
|------|------|
| `system_snapshot` | 系统快照 |
| `directory_snapshot` | 目录快照 |
| `app_state` | 应用状态 |
| `clipboard_get` / `clipboard_set` | 剪贴板（已纳入 mounted） |
| `recent_files` | 最近文件 |
| `environment_info` | 环境信息 |

---

## display 工具归属

`display` 用于将 File Service 中的文件引用加入 LLM 上下文，本身不访问 VM，只访问 File Service。因此已从 `vm` 类别移至新建的 `file` 类别。目前 `file` 类别仅包含 `display`。

---

## 权限与路由

- **Gateway `proxy_vm_tool`**：仅对 `desktop`、`shell`、`file` 做 `mounted_tools` 校验
- **browser / window / context**：不校验 `mounted_tools`，只要有 VM binding 即可调用
- 若需将 browser/window/context 纳入 mounted 控制，需在 `agent_binding.py` 的 `SUPPORTED_MOUNTED_TOOLS` 中扩展
