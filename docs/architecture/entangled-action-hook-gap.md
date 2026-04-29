# Entangled Action Hook — 实现文档

> 设计意图：Entangled 作为 Client 的"量子纠缠分身"，代替 Client 接收所有变更、代替 Client 执行 action。Client 只和 Entangled 对话，不感知 Gateway 的存在。
>
> **状态：已实现并部署** (2026-04-13)

## 目标架构

```
Client ──WS纠缠──→ Entangled Server ──hook回调──→ Gateway（业务实现）
                    ┌─ CRUD: 直接执行
                    ├─ sync: 维护状态、推送变更
                    └─ custom action: 转发给 Gateway hook → 返回结果给 Client
```

## 现状

### ✅ 已完成


| 能力                                               | 状态                                                                     |
| ------------------------------------------------ | ---------------------------------------------------------------------- |
| Client ↔ Entangled WS 直连                         | ✅ `EntangledSyncBridge` via `wss://api.gradievo.com/entangled/v1/sync` |
| subscribe / sync / entities_changed              | ✅ WsTransport → local cache → React Query                              |
| CRUD (create/update/delete/upsert) via WS action | ✅ `_dispatch_action_blocking` in `ws_handler.py`                       |
| Schema 注册 (DDL/字段/同步元数据)                         | ✅ `POST /v1/schema/register` via `schema_push.py`                      |
| Nginx 代理 Entangled WS                            | ✅ `/entangled/` → `127.0.0.1:19900`                                    |


### ❌ 缺失：Custom Action Hook 机制

Client 发送 `{type: "action", op: "refresh", entity: "api-key-models"}` → Entangled 收到 → `store.action()` → `**defn.actions` 为空 → KeyError**。

原因：Gateway 的 custom action handler（Python callable）注册在 Gateway 进程内存中，没有传递给 Entangled。

## Gap 详情

### Gap 1: Schema 注册不包含 action 信息

`**SqlEntityDef.to_spec()`** 序列化的字段：

```
name, table, id_field, user_scoped, key_params, fields, constraints,
default_order, lock_type, auto_timestamps, sync_type, sync_limit,
op_log_size, subscription_mode, data_order, default_not_in_filters, parent
```

**缺失：** `actions` — 没有 action 名称、没有 hook URL。

`**from_spec()`** 重建 `SqlEntityDef` 时 `actions` 始终为 `dict()`。

### Gap 2: EntityDef 没有 hook URL 字段

`Entangled/packages/server-python/entangled/server/defs.py`:

```python
actions: Dict[str, ActionFn] = field(default_factory=dict)
# ActionFn = Callable  —— 只支持本地 Python callable，不支持远程 URL
```

**缺失：** 类似 `action_hooks: Dict[str, str]` 的字段，用于存储 `{action_name: callback_url}`。

### Gap 3: Entangled 没有 action 转发逻辑

`Entangled/.../entity_store.py` 的 `action()` 方法：

```python
async def action(self, entity, user_id, action_name, params, payload):
    defn = self.get_def(entity)
    if not defn.actions or action_name not in defn.actions:
        raise KeyError(f"No action handler for '{action_name}' on '{entity}'")
    handler = defn.actions[action_name]
    # 只执行本地 callable
```

**缺失：** 当 `defn.actions` 中找不到本地 handler 时，检查是否有注册的 hook URL，通过 HTTP 回调 Gateway。

### Gap 4: Gateway 没有 action 回调 HTTP 端点

Gateway 的 `RemoteEntityStore.action()` 执行本地 handler，但没有暴露一个通用的 HTTP endpoint 让 Entangled 回调：

```
POST /internal/entity/{entity}/action/{action_name}
Body: { user_id, params, payload }
→ Response: { success, data }
```

**缺失：** 这个端点不存在。

### Gap 5: EntangledServiceClient 不传递 action 信息

`novaic-common/common/entangled_client.py` 的 `register_schema()` 只发送 `to_spec()` 的结果。

**缺失：** action hook 注册方法，如 `register_action_hooks(entity, hooks: Dict[str, str])`。

## 受影响的 Action 清单

共 **10 个实体、38 个自定义 action**，全部注册在 Gateway 侧：


| 实体                 | Action 名称                                                                                                                                                                           | 文件                    |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `agents`           | `interrupt`, `init`, `get_model`, `prompts_preview`, `available_images`                                                                                                             | `defs.py`             |
| `devices`          | `grouped`, `setup`, `start`, `stop`, `vm_start`, `vm_stop`, `android_start`, `android_stop`, `webrtc_stop`, `get_status`, `get_subjects`, `get_tool_capabilities`, `android_status` | `defs.py`             |
| `vm-users`         | `restart_vnc`                                                                                                                                                                       | `defs.py`             |
| `skills`           | `match`, `fork`, `get_tool_categories`, `get_agent_skills`, `set_agent_skills`, `get_agent_tools_config`, `save_agent_tools_config`                                                 | `defs.py`             |
| `api-keys`         | `test`                                                                                                                                                                              | `defs.py`             |
| `messages`         | `send`, `mark_all_read`, `clear`                                                                                                                                                    | `defs_stream.py`      |
| `execution-logs`   | `clear`                                                                                                                                                                             | `defs_stream.py`      |
| `log-payloads`     | `get_input`, `get_payload`                                                                                                                                                          | `defs_stream.py`      |
| `user-preferences` | `get_config`, `cleanup`                                                                                                                                                             | `defs_users.py`       |
| `models`           | `add_custom`                                                                                                                                                                        | `defs_models.py`      |
| `api-key-models`   | `refresh`, `remove`                                                                                                                                                                 | `defs_models.py`      |
| `available-models` | `toggle`                                                                                                                                                                            | `defs_models.py`      |
| `agent-tools`      | `get_bootstrap`, `save_bootstrap`                                                                                                                                                   | `defs_agent_forms.py` |


## 需要补全的链路

```
1. Schema 注册时携带 action hook 信息
   Gateway to_spec() ─→ { ..., actions: { "refresh": "/internal/entity/api-key-models/action/refresh" } }
   Entangled from_spec() ─→ 存储 hook URL

2. Entangled 收到 custom action 时转发
   store.action() ─→ 本地 handler 不存在
                   ─→ 检查 action_hooks[action_name]
                   ─→ HTTP POST 回调 Gateway
                   ─→ 返回结果给 Client

3. Gateway 暴露 action 回调端点
   POST /internal/entity/{entity}/action/{action_name}
   Body: { user_id, params, payload }
   ─→ RemoteEntityStore.action()
   ─→ Response: { success, data }
```

### 改动范围


| 组件                                             | 改动                                                     |
| ---------------------------------------------- | ------------------------------------------------------ |
| `entangled/server/defs.py`                     | `EntityDef` 增加 `action_hooks: Dict[str, str]` 字段       |
| `entangled/sql/entity_def.py`                  | `to_spec()` / `from_spec()` 序列化/反序列化 `action_hooks`    |
| `entangled/sql/entity_store.py`                | `action()` fallback 到 HTTP hook 转发                     |
| `novaic-gateway/gateway/entity/schema_push.py` | `to_spec()` 中包含 action hook URL                        |
| `novaic-gateway/main_gateway.py`               | 新增 `/internal/entity/{entity}/action/{action_name}` 路由 |
| `novaic-gateway/gateway/entity/store.py`       | 实现 action 回调 handler                                   |


### 不需要改动


| 组件                                     | 原因                                             |
| -------------------------------------- | ---------------------------------------------- |
| Rust client (`entangled_sync.rs`)      | 仍然发 `{type: "action"}` 到 Entangled WS，无变化      |
| 前端 TS (`dispatch.ts` / `client.ts`)    | 调用方式不变                                         |
| Entangled WS handler (`ws_handler.py`) | `_dispatch_action` 已正确路由到 `store.action()`，无需改 |
| Entangled CRUD                         | 不受影响                                           |

