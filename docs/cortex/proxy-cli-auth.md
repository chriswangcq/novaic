# Business 代理、CLI 与认证

> 源码：`novaic_cortex/proxy.py`（**`BusinessProxy`**）、`cli.py`（**`novaic`**）、`auth.py`（**能力 JWT**）。

## 1. 能力 JWT（Cortex 自签）

- **环境变量**：**`CORTEX_JWT_SECRET`**（默认开发用占位，生产必须改）。  
- **签发**：**`issue_capability_token`**；校验：**`verify_capability_token`**。  
- **Claims**：`user_id`、`agent_id`、`scope_id`、`permissions`、`exp`、`iss: novaic-cortex`。  
- **用途**：Sandbox / CLI 调 **`/v1/*`** 时在 **`Authorization: Bearer ...`** 中携带。  
- **签发端点**：**`POST /v1/token`**（body 含 `user_id`、`agent_id`、`scope_id` 等），**不需要**已有 Bearer。

与 **Gateway 的用户 JWT** 不同：**不同 secret、不同 claims**（见 `auth.py` 模块注释）。

---

## 2. BusinessProxy（服务间信任）

- **目的**：Cortex 作为旧 CLI 的入口，仅保留 `chat`、设备/VM 与 subagent 代理面；`memory`、`notebook`、`task`、`search` 已从 Cortex 代理面删除。  
- **环境变量**：**`BUSINESS_INTERNAL_URL`**（默认 `http://localhost:19998`）、**`CORTEX_INTERNAL_KEY`** → 请求头 **`X-Internal-Key`**。  
- **额外头**：**`X-User-Id`**、**`X-Agent-Id`**。  
- **不转发**能力 JWT：Business 侧用 internal key 建立信任（见 `proxy.py` 注释）。

HTTP 封装：**`POST /v1/proxy/{command}`**（见 [http-api.md](http-api.md)）→ **`BusinessProxy.proxy_command`**。

---

## 3. `novaic` CLI

- **环境变量**：**`NOVAIC_API`**（默认 `http://localhost:19996`）、**`NOVAIC_TOKEN`**（能力 JWT）。  
- **认知类**（直打 Cortex）：`read`、`write`、`ls`、`tools` → 对应 **`/v1/read`** 等。
- **代理类**（经 Proxy）：`chat`、`browser`、`screenshot`、`keyboard`、`mouse`、`shell_exec`、`qemu`、`subagent` → **`POST /v1/proxy/{command}`**。
- Cortex CLI 不再暴露 `memory`、`notebook`、`task`、`search`；需要这些业务能力时应由对应 owning service/package 提供入口。

---

## 4. 与本地 Sandbox 的对比

| 执行环境 | 路径 |
|----------|------|
| **本地文件 shell** | `Sandbox.exec`（[sandbox-shell.md](sandbox-shell.md)） |
| **VM / 设备 shell** | Business internal VM API，经 **`/v1/proxy/...`**，**不是** `sandbox.py` |

---

## 相关

- [proxy-gateway-routes.md](proxy-gateway-routes.md) — `command` → Business 路径表  
- [http-api.md](http-api.md)  
- [sandbox-shell.md](sandbox-shell.md)  
