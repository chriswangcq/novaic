# Phase 4 — 多用户改造（Multi-User SaaS）

> 目标：将 NovAIC 从单用户本地工具升级为支持多用户的 SaaS 平台。  
> 每个用户的数据（agents、消息、VM、配置）完全隔离，  
> 通过 JWT + nginx 注入的 `X-User-ID` 在 Gateway 全链路传递用户身份。
>
> **重要：** DB Schema v44~v47 已经实现（`agents.user_id`、`users`/`refresh_tokens` 表、`auth.py`）。  
> Phase 4 的主要工作是：nginx 配置、API 层 ownership 校验补全、前端登录 UI。

---

## 一、现状盘点

### 已完成（DB & 后端基础）

| 组件 | 状态 | 版本 |
|---|---|---|
| `agents.user_id` 字段 | ✅ 已实现 | v44 |
| `api_keys / ssh_keys / skills / config` 加 `user_id` | ✅ 已实现 | v44 |
| `users` 表（email/password/display_name） | ✅ 已实现 | v45 |
| `refresh_tokens` 表 | ✅ 已实现 | v45 |
| `POST /auth/register` / `POST /auth/login` | ✅ 已实现 | auth.py |
| `POST /auth/refresh` / `GET /auth/me` | ✅ 已实现 | auth.py |
| `GET /internal/auth/validate`（nginx auth_request） | ✅ 已实现 | auth.py |
| `get_current_user` FastAPI 依赖 | ✅ 已实现 | deps.py |
| `check_agent_access` ownership 校验 | ✅ 已实现 | deps.py |
| Clerk JWT 验证支持（可选） | ✅ 已实现 | auth.py |

### 待完成（Phase 4 工作）

| 组件 | 状态 | 优先级 |
|---|---|---|
| nginx JWT auth_request 配置 | ⬜ 待实现 | P0 |
| API 层 ownership 校验补全（Chat/Logs/VM/Device） | ⬜ 待实现 | P0 |
| `pc_client.py` 改为 per-device（Phase 1 完成后自动满足） | ⬜ Phase 1 完成 | P1 |
| SSE 广播反向索引优化 | ⬜ 待实现 | P1 |
| 存量数据 user_id 归属（data migration） | ⬜ 待实现 | P0 |
| 前端登录 UI（注册/登录/刷新 token） | ⬜ 待实现 | P0 |
| App JWT 管理（localStorage + Rust 同步） | ⬜ 待实现 | P0 |
| IndexedDB 按用户隔离 | ⬜ 待实现 | P1 |
| localStorage 按用户隔离 | ⬜ 待实现 | P1 |

---

## 二、身份传递链（已设计）

```
用户登录 → App 获取 access_token (JWT HS256 / Clerk RS256)
  ↓ 每次 API 请求
Authorization: Bearer <access_token>
  ↓ nginx auth_request
GET /internal/auth/validate
  → 验证 JWT 签名 + 过期
  → 返回 200 + header X-User-ID: <user_id>
  ↓ nginx proxy_set_header
X-User-ID: <user_id>
  ↓ Gateway FastAPI
Depends(get_current_user) → user_id
  ↓ 所有路由
check_agent_access(agent_id, user_id, db)
```

---

## 三、Task 1：nginx 配置

> 注意：这是部署层配置，需要在服务器 nginx 上操作，不在代码仓库中。  
> 记录在此供运维参考。

**文件：** `/etc/nginx/conf.d/novaic.conf`（生产服务器）

```nginx
# ---- auth_request 子请求 ----
location /internal/auth/validate {
    internal;
    proxy_pass         http://127.0.0.1:19999/internal/auth/validate;
    proxy_method       GET;
    proxy_set_header   Authorization $http_authorization;
    proxy_set_header   Content-Length "";
    proxy_pass_request_body off;
}

# ---- 主 API 路由（需要认证）----
location /api/ {
    # 先清空客户端可能伪造的 X-User-ID
    proxy_set_header   X-User-ID "";
    
    # JWT 验证（非阻塞，验证失败直接返回 401）
    auth_request       /internal/auth/validate;
    auth_request_set   $auth_user_id $upstream_http_x_user_id;
    
    # 将 Gateway 返回的 user_id 注入请求
    proxy_set_header   X-User-ID $auth_user_id;
    proxy_set_header   Authorization $http_authorization;
    
    proxy_pass         http://127.0.0.1:19999;
}

# ---- 内部敏感端点：仅本地可访问 ----
location ~* ^/api/(config/internal|vm/ssh/private-key) {
    allow 127.0.0.1;
    deny  all;
    proxy_pass http://127.0.0.1:19999;
}

# ---- 认证端点：不需要 JWT ----
location /auth/ {
    proxy_pass http://127.0.0.1:19999;
}

# ---- WebSocket（CloudBridge）：特殊处理 ----
location /internal/pc/ws {
    proxy_set_header   X-User-ID "";
    auth_request       /internal/auth/validate;
    auth_request_set   $auth_user_id $upstream_http_x_user_id;
    proxy_set_header   X-User-ID $auth_user_id;
    
    proxy_pass         http://127.0.0.1:19999;
    proxy_http_version 1.1;
    proxy_set_header   Upgrade $http_upgrade;
    proxy_set_header   Connection "upgrade";
    proxy_read_timeout 3600s;
}
```

### 本地开发模式（无 nginx）

本地开发时没有 nginx，`X-User-ID` 直接由前端发送（仅开发模式）：

```python
# deps.py — 开发模式兼容
import os

async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> str:
    # 生产：X-User-ID 来自 nginx 注入
    if x_user_id:
        return x_user_id
    
    # 开发模式：直接解析 JWT（仅在 DEV_MODE=true 时）
    if os.environ.get("DEV_MODE") == "true" and authorization:
        token = authorization.removeprefix("Bearer ").strip()
        try:
            from gateway.api.auth import decode_access_token
            payload = decode_access_token(token)
            return payload["sub"]  # user_id
        except Exception:
            pass
    
    raise HTTPException(status_code=401, detail="Unauthorized")
```

---

## 四、Task 2：API Ownership 校验补全

### 2.1 Chat 类端点

**文件：** `novaic-gateway/gateway/api/agents.py`（或 chat 相关路由文件）

```python
# 所有 Chat 端点加 check_agent_access

@router.get("/api/chat/history")
async def get_chat_history(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    check_agent_access(agent_id, user_id, db)
    # ... 原有逻辑 ...

@router.post("/api/chat/send")
async def send_message(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    check_agent_access(agent_id, user_id, db)
    # ...

# GET /api/chat/messages (SSE)
@router.get("/api/chat/messages")
async def chat_sse(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    check_agent_access(agent_id, user_id, db)
    # ...
```

### 2.2 Logs 类端点

```python
@router.get("/api/logs/entries")
async def get_log_entries(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    check_agent_access(agent_id, user_id, db)

@router.get("/api/logs/entry/{log_id}/input")
async def get_log_input(
    log_id: int,
    agent_id: str,  # 调用方需传 agent_id
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    check_agent_access(agent_id, user_id, db)
```

### 2.3 VM 类端点（Device 反查）

```python
# vm.py — Device 端点通过 device_id → agent_id → user_id 反查

from gateway.db.repositories.device import DeviceRepository

def check_device_access(device_id: str, user_id: str, db) -> dict:
    """通过 device_id 反查 agent.user_id 进行 ownership 校验。"""
    device_repo = DeviceRepository(db)
    device = device_repo.get(device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    
    agent_repo = AgentRepository(db)
    agent = agent_repo.get_agent(device.agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    if agent.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    return device

@router.post("/api/devices/{device_id}/start")
async def start_device(
    device_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    device = check_device_access(device_id, user_id, db)
    # ... 原有逻辑 ...
```

### 2.4 全局资源过滤

```python
# api_keys 示例
@router.get("/api/config/api-keys")
async def get_api_keys(
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = ApiKeyRepository(db)
    return repo.list_by_user(user_id)  # WHERE user_id = ?

# VM 列表过滤
@router.get("/api/vm/status")
async def get_vm_status(
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    agent_repo = AgentRepository(db)
    # 只返回当前用户的 agents
    agents = agent_repo.list_agents(user_id=user_id)
    # ...
```

---

## 五、Task 3：SSE 广播反向索引优化

**文件：** `novaic-gateway/gateway/sse_state.py`

### 问题

当前 SSE 广播会推给所有订阅者，再在 `event_generator` 里过滤：

```python
# 当前：全推
for queue in _chat_subscribers.values():
    await queue.put(event)
# event_generator 里：if event.agent_id != my_agent_id: skip
```

100 个在线用户时，每条消息进入 100 个 queue，99% 是无效投递。

### 优化：反向索引

```python
# sse_state.py

from typing import Dict, Set
import asyncio

# 订阅者 queue 表
_chat_subscribers: Dict[str, asyncio.Queue] = {}   # subscriber_id → queue
_log_subscribers: Dict[str, asyncio.Queue] = {}

# 反向索引：agent_id → 关注它的 subscriber_id 集合
_chat_agent_index: Dict[str, Set[str]] = {}
_log_agent_index: Dict[str, Set[str]] = {}


def subscribe_chat(subscriber_id: str, agent_id: str) -> asyncio.Queue:
    q = asyncio.Queue(maxsize=200)
    _chat_subscribers[subscriber_id] = q
    _chat_agent_index.setdefault(agent_id, set()).add(subscriber_id)
    return q


def unsubscribe_chat(subscriber_id: str, agent_id: str) -> None:
    _chat_subscribers.pop(subscriber_id, None)
    if agent_id in _chat_agent_index:
        _chat_agent_index[agent_id].discard(subscriber_id)
        if not _chat_agent_index[agent_id]:
            del _chat_agent_index[agent_id]


async def broadcast_chat_event(agent_id: str, event: dict) -> None:
    """只推给关注 agent_id 的订阅者，O(k) 而非 O(n)。"""
    subscribers = _chat_agent_index.get(agent_id, set())
    for sub_id in list(subscribers):
        q = _chat_subscribers.get(sub_id)
        if q is not None:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # 慢消费者丢弃
```

---

## 六、Task 4：存量数据迁移

现有数据库中 `user_id = ''`（空字符串），需要归属给具体用户。

### 迁移脚本

**文件：** `novaic-gateway/scripts/migrate_user_data.py`（新建，一次性运行）

```python
"""
存量数据 user_id 归属脚本。

运行方式：
  python scripts/migrate_user_data.py --user-id <user_id> --db-path gateway.db

作用：
  将所有 user_id='' 的 agents、api_keys、ssh_keys、skills、config
  归属到指定 user_id。
"""
import argparse
import sqlite3
import sys


def migrate(db_path: str, target_user_id: str, dry_run: bool = True):
    conn = sqlite3.connect(db_path)
    try:
        tables = [
            ("agents", "id"),
            ("api_keys", "id"),
            ("ssh_keys", "id"),
            ("skills", "id"),
        ]
        
        for table, pk in tables:
            # 统计影响行数
            cursor = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE user_id = ''",
            )
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} rows will be updated")
            
            if not dry_run:
                conn.execute(
                    f"UPDATE {table} SET user_id = ? WHERE user_id = ''",
                    (target_user_id,)
                )
        
        # config 表（复合 PK）
        cursor = conn.execute(
            "SELECT COUNT(*) FROM config WHERE user_id = ''"
        )
        count = cursor.fetchone()[0]
        print(f"  config: {count} rows will be updated")
        if not dry_run:
            conn.execute(
                "UPDATE config SET user_id = ? WHERE user_id = ''",
                (target_user_id,)
            )
        
        if dry_run:
            print("\n[DRY RUN] No changes made. Re-run with --execute to apply.")
        else:
            conn.commit()
            print(f"\n[DONE] Migrated all data to user_id={target_user_id}")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True, help="Target user_id")
    parser.add_argument("--db-path", default="gateway.db")
    parser.add_argument("--execute", action="store_true", help="Actually apply changes")
    args = parser.parse_args()
    
    migrate(args.db_path, args.user_id, dry_run=not args.execute)
```

### 上线顺序

```
Step 1: 部署 Gateway（schema v47 已兼容，allow_empty user_id）
Step 2: 运行迁移脚本（dry-run 确认后执行）
        python scripts/migrate_user_data.py \
            --user-id <admin_user_uuid> \
            --db-path /data/gateway.db \
            --execute
Step 3: 配置 nginx JWT 验证（auth_request）
Step 4: 发布 App 新版本（含登录 UI）
Step 5: 关闭 DEV_MODE（强制校验 X-User-ID）
```

---

## 七、Task 5：前端登录 UI

**文件：** `novaic-app/src/components/Auth/`（新建目录）

### 页面结构

```
App.tsx
  ├── isSignedIn=true  → 主界面（现有 Layout）
  └── isSignedIn=false → AuthPage（新建）
        ├── LoginForm
        └── RegisterForm
```

### AuthPage.tsx

```typescript
// novaic-app/src/components/Auth/AuthPage.tsx
import { useState } from 'react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  
  return (
    <div className="min-h-screen bg-nb-bg flex items-center justify-center">
      <div className="w-full max-w-md px-8 py-10 bg-nb-surface rounded-2xl border border-nb-border shadow-2xl">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-nb-text">NovAIC</h1>
          <p className="text-nb-text-muted mt-1 text-sm">AI 工作站</p>
        </div>
        
        {/* Tab 切换 */}
        <div className="flex mb-6 bg-nb-bg rounded-lg p-1">
          <button
            className={`flex-1 py-2 text-sm rounded-md transition-colors ${
              mode === 'login' 
                ? 'bg-nb-surface text-nb-text shadow-sm' 
                : 'text-nb-text-muted hover:text-nb-text'
            }`}
            onClick={() => setMode('login')}
          >
            登录
          </button>
          <button
            className={`flex-1 py-2 text-sm rounded-md transition-colors ${
              mode === 'register' 
                ? 'bg-nb-surface text-nb-text shadow-sm' 
                : 'text-nb-text-muted hover:text-nb-text'
            }`}
            onClick={() => setMode('register')}
          >
            注册
          </button>
        </div>
        
        {mode === 'login' ? <LoginForm /> : <RegisterForm onSuccess={() => setMode('login')} />}
      </div>
    </div>
  );
}
```

### LoginForm.tsx

```typescript
// novaic-app/src/components/Auth/LoginForm.tsx
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export function LoginForm() {
  const { login, isLoading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(email, password);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-sm text-nb-text-muted block mb-1">邮箱</label>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          className="w-full px-3 py-2 bg-nb-bg border border-nb-border rounded-lg text-nb-text text-sm focus:outline-none focus:ring-1 focus:ring-nb-accent"
          placeholder="you@example.com"
          required
        />
      </div>
      <div>
        <label className="text-sm text-nb-text-muted block mb-1">密码</label>
        <input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          className="w-full px-3 py-2 bg-nb-bg border border-nb-border rounded-lg text-nb-text text-sm focus:outline-none focus:ring-1 focus:ring-nb-accent"
          placeholder="••••••••"
          required
        />
      </div>
      {error && (
        <p className="text-red-400 text-xs">{error}</p>
      )}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-2.5 bg-nb-accent text-white rounded-lg text-sm font-medium hover:bg-nb-accent/90 disabled:opacity-50 transition-colors"
      >
        {isLoading ? '登录中...' : '登录'}
      </button>
    </form>
  );
}
```

---

## 八、Task 6：App JWT 管理

**文件：** `novaic-app/src/services/auth.ts`（已有，扩展）

### 当前状态

现有 `auth.ts` 已实现 JWT 存储（localStorage）和刷新逻辑。  
需要补充：

1. 调用 NovAIC Gateway 的 `/auth/login` / `/auth/refresh` 接口（不用 Clerk）
2. 登录后同步 token 到 Rust（`update_cloud_token` 命令）
3. IndexedDB 数据库切换（用 `user_id` 作为 DB 命名空间）

### useAuth hook

```typescript
// novaic-app/src/components/hooks/useAuth.ts
import { useCallback, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { setToken, clearToken, scheduleRefresh } from '../../services/auth';
import { closeDb, openAppDb } from '../../db';
import { useStore } from '../../app/store';

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:19999';

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: { id: string; email: string; display_name: string };
}

export function useAuth() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setUser = useStore(s => s.setUser);
  const setSignedIn = useStore(s => s.setSignedIn);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${GATEWAY_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || '登录失败');
      }
      const data: LoginResponse = await resp.json();
      
      // 1. 保存 token
      setToken(data.access_token, data.refresh_token);
      
      // 2. 通知 Rust（CloudBridge 需要 token）
      await invoke('update_cloud_token', { token: data.access_token });
      
      // 3. 打开对应用户的 IndexedDB
      await openAppDb(data.user.id);
      
      // 4. 更新 Zustand store
      setUser(data.user);
      setSignedIn(true);
      
      // 5. 启动 token 定时刷新
      scheduleRefresh();
    } catch (e: any) {
      setError(e.message || '登录失败');
    } finally {
      setIsLoading(false);
    }
  }, [setUser, setSignedIn]);

  const logout = useCallback(async () => {
    clearToken();
    await invoke('update_cloud_token', { token: '' });
    await closeDb();
    setUser(null);
    setSignedIn(false);
  }, [setUser, setSignedIn]);

  return { login, logout, isLoading, error };
}
```

---

## 九、Task 7：IndexedDB 按用户隔离

**文件：** `novaic-app/src/db/index.ts`

### 当前问题

DB 名称固定为 `novaic-db`，不同用户共用同一个 IndexedDB：

```typescript
// 当前
const db = await openDB('novaic-db', DB_VERSION, { ... });
```

### 目标

```typescript
// 目标：DB 名称包含 user_id
const db = await openDB(`novaic-db-${userId}`, DB_VERSION, { ... });
```

### 改动

```typescript
// db/index.ts
let _db: IDBPDatabase | null = null;
let _currentUserId: string | null = null;

export async function openAppDb(userId: string): Promise<IDBPDatabase> {
  // 如果切换用户，先关闭旧 DB
  if (_db && _currentUserId !== userId) {
    _db.close();
    _db = null;
  }
  
  if (_db) return _db;
  
  _currentUserId = userId;
  _db = await openDB(`novaic-db-${userId}`, DB_VERSION, {
    upgrade(db, oldVersion, newVersion) {
      // ... 现有 upgrade 逻辑不变 ...
    },
  });
  return _db;
}

export function closeDb(): void {
  _db?.close();
  _db = null;
  _currentUserId = null;
}
```

---

## 十、Task 8：localStorage 按用户隔离

**文件：** `novaic-app/src/app/store.ts`

```typescript
// 当前（用户无关的 key）
const STORAGE_KEYS = {
  SELECTED_AGENT: 'novaic_selected_agent',
  SELECTED_MODEL: 'novaic_selected_model',
  LAYOUT_V2: 'novaic_layout_v2',
};

// 目标（带 user_id 前缀）
function storageKey(key: string, userId: string): string {
  return `novaic_${userId}_${key}`;
}

// store 初始化时，从用户对应的 key 读取
const userId = useStore.getState().user?.id ?? 'anonymous';
const selectedAgent = localStorage.getItem(storageKey('selected_agent', userId));
```

---

## 十一、完整上线顺序

```
Phase 4 上线流程（生产环境）

Step 0: 确认 DB 已在 v47（检查 config 表 version 字段）
        SELECT value FROM config WHERE user_id='' AND key='version';

Step 1: 部署 Gateway（含 auth.py、deps.py 的最新版本）
        → 开启 DEV_MODE=true（暂时跳过 nginx 校验）
        → 运行数据库创建用户：
          POST /auth/register {"email":"admin@novaic.ai","password":"...","display_name":"Admin"}

Step 2: 运行存量数据迁移脚本（将 user_id='' 归属给 admin 用户）
        python scripts/migrate_user_data.py \
            --user-id <admin_user_id_from_step1> \
            --db-path /data/gateway.db \
            --execute

Step 3: 配置 nginx auth_request
        → 测试：curl -H "Authorization: Bearer <jwt>" https://api.gradievo.com/api/agents
        → 确认返回 200 且数据正确

Step 4: 关闭 DEV_MODE，重启 Gateway
        → 所有 /api/* 请求必须携带有效 JWT

Step 5: 发布 App v2.0（含登录 UI）
        → 现有用户：用 admin 账号登录即可（存量数据已归属）
        → 新用户：注册后自动创建空白 workspace
```

---

## 十二、安全要点

### X-User-ID 不可被前端伪造

```nginx
# nginx 必须先清空客户端传来的 X-User-ID，再注入自己解析的值
proxy_set_header X-User-ID "";          # ← 清空！
# auth_request 之后赋值：
auth_request_set $auth_user_id $upstream_http_x_user_id;
proxy_set_header X-User-ID $auth_user_id;
```

### JWT Secret 强制从环境变量读取

```bash
# 生产环境：
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
# 不得硬编码在代码中！
```

### refresh_token 单次使用（已实现）

现有 `POST /auth/refresh` 在换 token 时会生成新 refresh_token 并删除旧的（已实现），无需重复做。

---

## 十三、完成标准

Phase 4 完成的判断标准：

1. ✅ nginx auth_request 配置正确，未登录请求返回 401
2. ✅ 所有 Chat/Log/VM/Device 端点通过 `check_agent_access` / `check_device_access` 校验
3. ✅ 存量数据已归属给正确用户，`user_id != ''`
4. ✅ 前端登录/注册 UI 正常工作，token 自动刷新
5. ✅ IndexedDB 和 localStorage 按用户隔离，切换账号不混数据
6. ✅ CloudBridge 登录后立即连接（Phase 1 完成后自动满足）
7. ✅ SSE 广播反向索引优化上线（可选，高流量时实施）
8. ⬜ 多用户并发测试：两个用户同时操作，数据互不干扰
