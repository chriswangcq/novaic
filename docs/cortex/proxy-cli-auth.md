# Gateway 代理、CLI 与认证

> 源码：`novaic_cortex/proxy.py`（**`GatewayProxy`**）、`cli.py`（**`novaic`**）、`auth.py`（**能力 JWT**）。

## 1. 能力 JWT（Cortex 自签）

- **环境变量**：**`CORTEX_JWT_SECRET`**（默认开发用占位，生产必须改）。  
- **签发**：**`issue_capability_token`**；校验：**`verify_capability_token`**。  
- **Claims**：`user_id`、`agent_id`、`scope_id`、`permissions`、`exp`、`iss: novaic-cortex`。  
- **用途**：Sandbox / CLI 调 **`/v1/*`** 时在 **`Authorization: Bearer ...`** 中携带。  
- **签发端点**：**`POST /v1/token`**（body 含 `user_id`、`agent_id`、`scope_id` 等），**不需要**已有 Bearer。

与 **Gateway 的用户 JWT** 不同：**不同 secret、不同 claims**（见 `auth.py` 模块注释）。

---

## 2. GatewayProxy（服务间信任）

- **目的**：Cortex 作为 Agent **唯一入口**；业务/设备/MCP 类请求转到 Gateway **`/internal/...`**。  
- **环境变量**：**`GATEWAY_INTERNAL_URL`**（默认 `http://localhost:19999`）、**`CORTEX_INTERNAL_KEY`** → 请求头 **`X-Internal-Key`**。  
- **额外头**：**`X-User-Id`**、**`X-Agent-Id`**。  
- **不转发**能力 JWT：Gateway 侧用 internal key 建立信任（见 `proxy.py` 注释）。

HTTP 封装：**`POST /v1/proxy/{command}`**（见 [http-api.md](http-api.md)）→ **`GatewayProxy.proxy_command`**。

---

## 3. `novaic` CLI

- **环境变量**：**`NOVAIC_API`**（默认 `http://localhost:19996`）、**`NOVAIC_TOKEN`**（能力 JWT）。  
- **认知类**（直打 Cortex）：`read`、`write`、`ls`、`recall`、`tools` → 对应 **`/v1/read`** 等。  
- **业务类**（经 Proxy）：如 `chat`、`search`、`memory ...` → **`POST /v1/proxy/{command}`**（见 `cli.py` 中 `cmd_chat`、`cmd_search` 等）。

---

## 4. 与本地 Sandbox 的对比

| 执行环境 | 路径 |
|----------|------|
| **本地文件 shell** | `Sandbox.exec`（[sandbox-shell.md](sandbox-shell.md)） |
| **VM / 设备 shell** | Gateway internal VM API，经 **`/v1/proxy/...`**，**不是** `sandbox.py` |

---

## 相关

- [http-api.md](http-api.md)  
- [sandbox-shell.md](sandbox-shell.md)  
