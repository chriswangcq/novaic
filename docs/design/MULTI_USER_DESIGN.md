# NovAIC 多用户改造设计文档

> 状态：设计阶段  
> 最后更新：2026-03-07

---

## 一、目标与范围

### 目标

将 NovAIC 从单用户本地桌面应用改造为支持多用户的云端 SaaS，做到：

1. **数据隔离**：每个用户只能访问自己的 agents、消息、日志、配置、API key、SSH key
2. **资源隔离**：VM / Android 设备归属用户，无法跨用户操作
3. **身份传递**：nginx 鉴权后将 `user_id` 注入 header，gateway 全链路使用

### 不在范围内（暂不做）

- 跨用户文件/TRS 结果共享权限（先做单用户隔离，共享功能后续迭代）
- 平台级 Admin 控制台
- 计费 / quota 系统

### 改动仓库

只需改动两个仓库：

| 仓库 | 改动内容 |
|---|---|
| `novaic-gateway` | DB schema、repositories、API ownership 校验、SSE、PcClientManager |
| `novaic-app` | 用户 auth 流程、localStorage 按用户隔离 |

storage-a / storage-b / tools-server / runtime-orchestrator / queue-service **均不需要改动**，隔离逻辑全收在 gateway 层。

---

## 二、身份传递方案

### 当前状态

nginx 只做单一静态 API key 校验（`Bearer YOUR_API_KEY`），不区分用户身份，gateway 没有任何 `user_id` 概念。

### 目标方案：JWT + nginx 注入 header

```
用户请求
  → nginx: 验证 JWT，解出 user_id
    → proxy_set_header X-User-ID $jwt_user_id
      → gateway: 从 X-User-ID header 读取 user_id，注入所有路由
```

**nginx 侧**（需单独升级，不在本文档范围内）：
```nginx
# 用 lua-resty-jwt 或 auth_request 子请求解析 JWT
proxy_set_header X-User-ID $jwt_user_id;
```

**gateway 侧**（本文档范围）：
```python
# FastAPI 依赖注入，所有路由复用
async def get_current_user(x_user_id: str = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-ID header")
    return x_user_id
```

> **注意**：`X-User-ID` 只能来自 nginx 注入，前端不得自行伪造。nginx 在转发时需删除客户端原始的同名 header：`proxy_set_header X-User-ID ""`（先清空再赋值）。

---

## 三、数据库 Schema 改动

### 3.1 agents 表加 user_id（核心）

```sql
ALTER TABLE agents ADD COLUMN user_id TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
```

`agents` 是所有数据的根表，其子表（`chat_messages`、`execution_logs`、`subagents`、`devices`、`tasks` 等）均通过 `agent_id FK` 级联。只要在 `agents` 层过滤 `user_id`，子表查询天然隔离，**子表不需要加 `user_id` 列**。

### 3.2 全局资源表加 user_id

这些表当前是全局共享的，需加 `user_id` 做用户隔离：

| 表 | 改动 |
|---|---|
| `api_keys` | 加 `user_id TEXT NOT NULL DEFAULT ''` |
| `ssh_keys` | 加 `user_id TEXT NOT NULL DEFAULT ''` |
| `config` | 加 `user_id TEXT NOT NULL DEFAULT ''`（每行是一个 key-value，需支持 per-user 覆盖） |
| `skills` | 加 `user_id TEXT NOT NULL DEFAULT ''`（或保留全局共享作为平台级资源，产品决策） |
| `candidate_models` | 加 `user_id TEXT NOT NULL DEFAULT ''` |

### 3.3 Schema 版本

当前 v43，本次改动升至 **v44**，migration 函数需处理存量数据（DEFAULT '' 占位，允许后续补填）。

---

## 四、Gateway 改动详情

### 4.1 新增依赖注入

**文件**：`novaic-gateway/main_gateway.py`（或新建 `gateway/api/deps.py`）

```python
from fastapi import Header, HTTPException, Depends

async def get_current_user(x_user_id: str = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-ID")
    return x_user_id

async def verify_agent_ownership(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    db = Depends(get_db),
) -> str:
    """确认 agent 归属当前用户，返回 agent_id"""
    repo = AgentRepository(db)
    agent = repo.get(agent_id)
    if not agent or agent.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Agent not found or access denied")
    return agent_id
```

### 4.2 Agent CRUD

**文件**：`novaic-gateway/gateway/api/agents.py`

| 端点 | 改动 |
|---|---|
| `GET /api/agents` | 加 `user_id` 过滤：`WHERE user_id = ?` |
| `POST /api/agents` | 创建时写入 `user_id = get_current_user()` |
| `GET /api/agents/{agent_id}` | 加 `Depends(verify_agent_ownership)` |
| `PATCH /api/agents/{agent_id}` | 同上 |
| `DELETE /api/agents/{agent_id}` | 同上 |
| `GET /api/agents/{agent_id}/*` | 所有子路由加 `Depends(verify_agent_ownership)` |

### 4.3 Chat / Logs / Agent 控制接口

这些接口目前通过 `agent_id` query param 访问，需加 ownership 校验：

```python
# 改动前
@app.get("/api/chat/history")
def get_chat_history(agent_id: str):
    ...

# 改动后
@app.get("/api/chat/history")
def get_chat_history(
    agent_id: str = verify_agent_ownership,  # 或 Depends
    user_id: str = Depends(get_current_user),
):
    ...
```

需要加校验的端点（完整列表）：

**Chat 类**
- `GET /api/chat/history`
- `GET /api/chat/messages` (SSE)
- `POST /api/chat/send`
- `GET /api/chat/pending-questions`
- `POST /api/chat/respond/{request_id}`

**Logs 类**
- `GET /api/logs/entries`
- `GET /api/logs/stream` (SSE)
- `GET /api/logs/entry/{log_id}/input`（需通过 log_id → agent_id 反查再验证）
- `GET /api/logs/clear`

**Agent 控制类**
- `POST /api/agent/interrupt`
- `POST /api/agent/rest`
- `POST /api/agent/wake`
- `GET /api/agent/inbox`
- `GET /api/agent/rest-state`

**VM 类**
- `GET /api/vm/status/{agent_id}`
- `POST /api/vm/start`（body 中有 agent_id）
- `POST /api/vm/stop`
- `POST /api/vm/setup`
- `GET /api/vm/{agent_id}/*`

**Device 类**（特殊）
- `POST /api/devices/{device_id}/setup|start|stop|status`：这些端点只有 `device_id`，没有 `agent_id`。需通过 `device_id → agent_id → user_id` 反查后校验。

### 4.4 全局资源接口加 user_id 过滤

| 端点组 | 改动 |
|---|---|
| `GET/POST/PATCH/DELETE /api/config/api-keys` | 所有操作限定 `user_id` |
| `GET/PATCH /api/config/settings` | per-user 配置 |
| `GET /api/vm/ssh/keys` / `pubkey` | per-user SSH key |
| `GET/POST/PUT/DELETE /api/skills` | per-user 或平台级（待定） |
| `GET /api/vm/status` / `running` | 只返回当前用户的 VM |
| `POST /api/vm/stop-all` | 只停当前用户的 VM |
| `POST /api/config/cleanup` | 只清理当前用户的孤立数据 |

### 4.5 内部 Worker 端点加网络隔离

这两个端点只被内部 Worker 调用，不应对用户开放，通过 nginx `location` block 限制 localhost-only：

| 端点 | 原因 |
|---|---|
| `GET /api/config/internal` | 返回所有 LLM API key 明文 |
| `GET /api/vm/ssh/private-key` | 返回 SSH 私钥 |

nginx 改动：
```nginx
location ~* ^/api/(config/internal|vm/ssh/private-key) {
    allow 127.0.0.1;
    deny  all;
    proxy_pass http://127.0.0.1:19999;
}
```

### 4.6 TRS 代理加 ownership 校验

**文件**：`novaic-gateway/main_gateway.py`（`proxy_trs` 函数，约 line 1950）

TRS 由 gateway 反向代理，ownership 校验在 gateway 层做，storage-b 不动：

```python
@app.api_route("/api/trs/{path:path}", methods=["GET", "POST"])
async def proxy_trs(
    path: str,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    # GET /{result_id}/for-llm 等读取请求：校验 result_id 归属
    if request.method == "GET":
        result_id = path.split("/")[0]
        # 通过 result_id 查 TRS 获取 agent_id，再验证 agent 归属用户
        await verify_trs_ownership(result_id, user_id)
    # POST /create 请求：写入时记录 user_id（可选，agent_id 已足够）
    ...
```

### 4.7 PcClientManager 改为 per-user

**文件**：`novaic-gateway/gateway/api/internal/pc_client.py`

```python
# 改动前：全局单例
_manager = PcClientManager()

def get_pc_client_manager() -> PcClientManager:
    return _manager

# 改动后：per-user dict
_managers: Dict[str, PcClientManager] = {}

def get_pc_client_manager(user_id: str) -> PcClientManager:
    if user_id not in _managers:
        _managers[user_id] = PcClientManager()
    return _managers[user_id]

# WebSocket endpoint 从 header 取 user_id
@router.websocket("/pc/ws")
async def pc_client_websocket(websocket: WebSocket):
    user_id = websocket.headers.get("x-user-id")
    if not user_id:
        await websocket.close(1008, "Missing X-User-ID")
        return
    manager = get_pc_client_manager(user_id)
    await websocket.accept()
    ...
    # 断开时清理（可选，避免空 manager 堆积）
    finally:
        await manager.disconnect(websocket)
        if not manager.is_connected and user_id in _managers:
            del _managers[user_id]
```

### 4.8 SSE 广播优化（反向索引）

**文件**：`novaic-gateway/gateway/sse_state.py`

现在广播是全推所有订阅者，再在 `event_generator` 里过滤。100 个在线用户时每条消息进 100 个 queue。

改为**反向索引**，广播时只推给关注对应 agent 的订阅者：

```python
# sse_state.py 新增
_chat_agent_index: Dict[str, set] = {}   # agent_id → {subscriber_ids}
_log_agent_index:  Dict[str, set] = {}   # agent_id → {subscriber_ids}
```

订阅时：
```python
_chat_subscribers[subscriber_id] = queue
_chat_agent_index.setdefault(agent_id, set()).add(subscriber_id)
```

取消订阅时：
```python
_chat_subscribers.pop(subscriber_id, None)
_chat_agent_index.get(agent_id, set()).discard(subscriber_id)
```

广播时：
```python
# 原来：O(所有用户)
for queue in _chat_subscribers.values():
    queue.put_nowait(message)

# 改后：O(1) —— 只推给关注这个 agent 的订阅者
for sid in _chat_agent_index.get(agent_id, set()):
    queue = _chat_subscribers.get(sid)
    if queue:
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            pass
```

`event_generator` 里的 `if message.get("agent_id") == agent_id` 过滤可同步删除（消息已保证只进对应 agent 的 queue）。

同样改动适用于 `_log_subscribers` / `_log_agent_index` 和 `broadcast_subagent_update`。

---

## 五、App 改动详情

### 5.1 用户 Auth 流程

**文件**：`novaic-app/src/services/auth.ts`

当前是读取 Tauri 本地 API key，多用户需改为真正的用户登录流程：

1. 未登录 → 跳转登录页（用户名/密码 或 OAuth）
2. 登录成功 → 服务端返回 JWT token
3. JWT 存入内存（不存 localStorage，防止 XSS）或 HttpOnly cookie
4. 所有 API 请求携带 `Authorization: Bearer <JWT>`，nginx 验证后注入 `X-User-ID`

### 5.2 localStorage 按用户隔离

**文件**：`novaic-app/src/store/index.ts`

当前 localStorage key：
```typescript
const STORAGE_KEYS = {
    SELECTED_AGENT: 'novaic_selected_agent',
    SELECTED_MODEL: 'novaic_selected_model',
    LAYOUT_V2: 'novaic_layout_v2',
}
```

改为带 user_id 前缀，防止同一台机器多用户互相干扰：
```typescript
function storageKey(key: string, userId: string) {
    return `novaic_${userId}_${key}`;
}
```

### 5.3 Zustand store 加 user 字段

**文件**：`novaic-app/src/store/index.ts`

```typescript
// 当前
user: null,

// 改为
user: {
    id: string,
    name: string,
    // ...其他用户信息
} | null,
```

登录后 `setUser(userInfo)`，登出时 `setUser(null)` 并清理 localStorage。

---

## 六、迁移策略

### 存量数据处理

Schema v43 → v44 migration 时，`user_id` 使用空字符串 `''` 作为默认值（而非 NOT NULL 无默认）：

```python
# gateway/db/schema.py migration 函数
def migrate_v43_to_v44(conn):
    conn.execute("ALTER TABLE agents ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
    conn.execute("ALTER TABLE api_keys ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
    conn.execute("ALTER TABLE ssh_keys ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
    conn.execute("ALTER TABLE config ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
    conn.execute("ALTER TABLE candidate_models ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id)")
```

存量 agent 的 `user_id = ''`，需要管理员通过脚本或界面手动归属给对应用户。

### 上线顺序

1. 部署 gateway v44（加 schema migration，`get_current_user` 依赖加 `allow_empty=True` 兼容模式）
2. 完成存量数据 user_id 归属
3. 升级 nginx（启用 JWT 验证 + `X-User-ID` 注入）
4. 关闭 gateway 的 `allow_empty` 兼容模式，强制校验 `X-User-ID`
5. 发布 App 新版本（含登录流程）

---

## 七、关键约束与注意点

### X-User-ID 不可被前端伪造

nginx 转发时必须先清空客户端可能带来的同名 header：

```nginx
proxy_set_header X-User-ID "";        # 先清空
# lua/auth_request 解析 JWT 后再赋值
proxy_set_header X-User-ID $jwt_user_id;
```

### 内部 Worker 请求不携带 X-User-ID

Worker（agent runtime）调用 gateway 的内部接口（`/api/logs/broadcast`、`/api/chat/event` 等）走 localhost，不经过 nginx，不携带 `X-User-ID`。这些端点本身就在 `/internal/` 或通过端口隔离，**不需要加 `get_current_user` 依赖**。

### device_id 端点需要反查 user_id

`POST /api/devices/{device_id}/start|stop|setup` 只有 `device_id`，需要：

```python
device = device_repo.get(device_id)
agent = agent_repo.get(device.agent_id)
if agent.user_id != current_user_id:
    raise HTTPException(403)
```

### TRS result_id 校验的性能

TRS ownership 校验需要查 TRS 数据库（storage-b），走一次 HTTP 请求到 `:19994`。读操作（`/for-llm`、`/preview`）调用频率高，可考虑在 gateway 层缓存 `result_id → agent_id` 的映射（TTL 5 分钟），避免每次都查 TRS。

---

## 八、待办 / 技术债（多用户专项）

- [ ] nginx 侧 JWT 验证方案选型（lua-resty-jwt vs auth_request vs OpenResty）
- [ ] 用户注册/登录 API（gateway 新增 `/api/auth/*` 或独立 auth service）
- [ ] Schema v44 migration 脚本及存量数据归属工具
- [ ] `skills` 表是 per-user 还是平台级共享（产品决策）
- [ ] TRS ownership 校验缓存层
- [ ] `POST /api/vm/stop-all` 改为只停当前用户的 VM（当前无 user 过滤）
- [ ] `POST /api/config/cleanup` 改为 per-user 孤立数据清理
- [ ] App 登录页 UI 设计与实现
- [ ] JWT refresh token 机制
