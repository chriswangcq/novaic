# `POST /v1/proxy/{command}` → Business

> 源码：`novaic_cortex/proxy.py`（**`_COMMAND_ROUTERS`**、**`BusinessProxy.proxy_command`**）。CLI：`novaic_cortex/cli.py`。

Cortex 在 **`Authorization: Bearer`**（能力 JWT）下接收 JSON body，按 **`command`** 转到 **Business Service**（`:19998`）**`/internal/...`**，请求头含 **`X-Internal-Key`**、**`X-User-Id`**、**`X-Agent-Id`**（见 [proxy-cli-auth.md](proxy-cli-auth.md)）。

> **边界约束（PR-75）**：Cortex 不再代理 `memory`、`notebook`、`task`、`search`。这些属于业务/记忆/任务域，不属于 Cortex 的 scope 树维护或 LLM context 拼装职责。

---

## 1. 命令 → Business 路径（摘要）

| `command` | 路由函数 | Business 路径模式（`*` 为 agent 相关） |
|-----------|----------|--------------------------------------|
| **`chat`** | `_route_chat` | `POST /internal/agents/{agent_id}/chat/event` |
| **`browser`** | `_route_browser` | `POST /internal/agents/{agent_id}/vm/browser/{action}` |
| **`screenshot`** | `_route_screenshot` | `POST /internal/agents/{agent_id}/vm/screenshot` |
| **`keyboard`** | `_route_keyboard` | `POST /internal/agents/{agent_id}/vm/keyboard` |
| **`mouse`** | `_route_mouse` | `POST /internal/agents/{agent_id}/vm/mouse` |
| **`shell_exec`** | `_route_shell_exec` | `POST /internal/agents/{agent_id}/vm/shell` |
| **`qemu`** | `_route_qemu` | `/internal/agents/{agent_id}/qemu/...` |
| **`subagent`** | `_route_subagent` | `/internal/agents/{agent_id}/subagent/...` 等 |

未知 **`command`**：**`400`**，`{"error":"Unknown command: ..."}`。

---

## 2. 与本地 Sandbox 的区别

| 执行环境 | 入口 |
|----------|------|
| **本机文件 shell** | **`Sandbox.exec`** / **`POST /v1/shell`**（[sandbox-shell.md](sandbox-shell.md)） |
| **远端 VM shell** | **`shell_exec`** → Business Service **`vm/shell`** |

---

## 相关

- [proxy-cli-auth.md](proxy-cli-auth.md)  
- [http-api.md](http-api.md)  
