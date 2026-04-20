# 常见问题与排障

> 与当前实现/已修复问题一致；对应原 **`HANDOVER.md` §十五**。新现象请查 Gateway、task-worker、AppBridge 日志。

## 问题速查表

| 问题 | 原因 | 解决 |
|------|------|------|
| **AppBridge 秒断 / `WS not connected (action=entity)`** | Gateway `/api/app/ws` handler 异常（客户端 RST）；曾见 `exists_before` → `KeyError: 'rowid'` | 部署 `store.py` 游标 **`AS _cf, AS _rid`**；`grep Message loop crashed gateway-*.log`，对齐 `[AppWS] accepted` / `handler exiting` |
| macOS SIGTRAP | enigo 键盘须在 main queue | 已改 CGEvent |
| **Entangled WS Message too long** | head_n 未 LIMIT，全量过大 | Gateway/Entangled 透传 `limit` |
| **UI 冻结 / Device tab 卡死** | `getCachedUser()` 每次新对象 → useEffect 死循环 | 依赖改为 **userId 字符串** |
| **宽屏消息不可见** | opacity-0 + `h-full` 高度为 0 | `flex-1 min-h-0` |
| Gateway 无响应 | WAL/SHM 损坏 | 停服务后删 `*.db-wal` / `*.db-shm`（谨慎） |
| Gateway 500 | `JWT_SECRET` 未设置 | 检查 `jwt_secret.env` |
| Gateway 写锁 | 写未在 transaction | `with db.transaction("global")` |
| Port **1420** 占用 | 上次 dev 未退出 | `kill $(lsof -ti:1420)` |
| App 一直 Connecting | pushToken 顺序 | 先 `await pushToken()` 再 initialize |
| Rust panic Cannot block | async 里 `blocking_read` | `read().await` |
| iOS 黑屏 | custom-protocol + WKWebView | 构建 `--features mobile` |
| `tauri ios run` 失败 | exportOptionsPlist | build + devicectl install |
| iOS arch 错 | FORCE_COLOR | `patch-ios-xcode.sh` |
| iOS aws-lc-sys | Xcode beta SDKROOT | 正式版 Xcode |
| LLM 429 / 超时 | 限流/过载 | task-worker 日志、退避 |
| 截图截错屏 | runtime_context 缺 display | 注入 display |
| scrcpy 无响应 | TCP 断未 break | write 失败 break |
| WebRTC 多端互踢 | stop_peers 等 | 见历史修复 |
| coturn 新连接失败 | 僵尸 session | 重启 coturn |
| Relay handshake timeout | open_bi | accept_bi |
| **agent-binding 保存后消失** | update 无行；nav 未订阅 agent-binding | upsert；nav 增加订阅；settings 传 agentId |
| **绑定 UI 与缓存不一致** | RQ stale、entity_get | `createFormStore` upsert 成功处理；`allowMissing` |
| **选无设备仍绑定** | `currentBinding` 被清空 | `bindingData?.device_id` 触发 clear |
| **执行日志条偏右** | Framer `transform` | `ChatPanel` flex 居中 + `px-4` |
| **device 浮窗不显示** | 读错数据源 | `agentBindingStore.useForm()` |
| **sync_contract_version 为 0** | schema 首包缺字段 | `app_client.py` 与 TS 解析 `{ entities, syncContractVersion }` |
| **选 Agent 状态异常** | `useCallback` 闭包 | `handleSelectAgent` / `handleAgentCreated` 依赖 **`agents`** |
| **登出仍弹设置** | `settingsOpen` | `handleLogout` 置 **`settingsOpen: false`** |
| **`PRAGMA wal_checkpoint(TRUNCATE)`** | 截断未提交事务 | **禁止运行时执行** |

## 跨服务按 scope_id 查问题（PR-24 LogContext，2026-04-15）

每条日志都多了 4 列：`scope_id=... agent_id=... user_id=... caller=...`。
拿一个 scope_id，可以在所有后端日志里串成一条完整时间线，不用再人肉
join 四份文件。

```bash
# 1. 从 trace 端点（PR-25）或者数据库拿一个 scope_id
SID="$(sqlite3 /opt/novaic/data/entangled.db \
  "SELECT claimed_by_scope FROM chat_messages
    WHERE claimed_by_scope IS NOT NULL
    ORDER BY created_at DESC LIMIT 1;")"
echo "scope_id=$SID"

# 2. 跨日志 grep — 时间顺序合并
cd /opt/novaic/data/logs
rg "scope_id=$SID" business-*.log queue-service-*.log cortex.log \
    runtime.log task-worker-*.log saga-worker-*.log health-*.log \
    | sort -k1,2
```

### 常见信号

| 现象 | 解读 |
|------|------|
| 只在 business 日志看到 scope_id | scope_id 在 session.init 之前就挂了（dispatcher 问题） |
| business + queue 有，cortex 没 | Cortex 调用失败或 scope create 出错 —— 看 cortex.log 同时段的 WARNING |
| cortex 有但 runtime 日志没后续 | saga/task worker 起不来或没领到 —— 查 queue-service `event=recover` |
| `caller=unknown` 出现在 /internal/ 路径 | 有服务没挂 `X-Internal-Service` —— 找违规 caller，补 internal_sync_client |

### 原理（一分钟）

- 发消息时，runtime `handle_session_init` 第一件事就是
  `common.log_context.bind(scope_id=..., agent_id=..., user_id=...)`。
- 之后所有 `httpx.Client` / `AsyncClient`（只要是
  `internal_sync_client` 创建的）在 outgoing 请求的 event_hook 里
  自动塞 `X-Scope-Id` / `X-Agent-Id` / `X-User-Id` Header。
- 每个服务的 `CallerLoggingMiddleware` 读到这三个 Header 就 bind 到
  `ContextVar`，handler 返回前 reset。
- stdlib `logging` 的 `ContextFilter` 把 ContextVar 的值注入每条
  LogRecord，formatter 就能打印出来了。

## Subagent 状态异常查因（PR-28 state machine，2026-04-15）

所有 `subagents.status` 写入都会经过
`business.internal.subagent_state.transition(...)`，留下一条固定格式的日志行：

```
subagent_state subagent=<subagent_id> <from_status> -> <to_status> reason=<reason> actor=<actor>
```

常见问题定位：

```bash
cd /opt/novaic/data/logs

# 1. 某 subagent 最近的状态流水
rg "subagent_state subagent=sub-xxxxxxxxxxxx" business-*.log | tail -50

# 2. 本周被 reject 的非法转移（409）
rg "InvalidTransition|completed -> awake|cancelled -> " business-*.log

# 3. 当前卡在某状态超过 N 分钟的 subagent（结合 last transition log line 时间戳）
rg "subagent_state" business-*.log | awk '{print $NF, $0}' | sort | tail
```

### 常见信号

| 现象 | 解读 |
|------|------|
| `reason=timeout actor=business.status_query` | `RUNNING → FAILED`，任务没在 `timeout_at` 前上报完成；查 task-worker 是否卡住 |
| `reason=interrupt actor=business.interrupt_agent` | 用户主动打断；正常链路 |
| 429/409 `completed -> awake` | 有调用方试图复活终态 subagent — 检查调用 caller；这是 bug |
| 某 subagent 长时间看不到新 transition | subagent 卡在中间态；查 runtime 对应 subagent 的 saga 状态 |

### 原理（一分钟）

- `subagent_state.py` 的 `ALLOWED` 矩阵明确规定每个状态允许的下一跳。终态
  `completed`/`cancelled` 出度为 0 —— 任何试图 "复活" 都会 `InvalidTransition`，
  业务层 409。
- 业务侧所有 `store.update("subagents", ..., {"status": ...})` 都被
  `scripts/ci/lint_subagent_status.sh` 禁止；必须走 `transition()` 或
  `mark_*()` 便捷 wrapper。
- Runtime 侧 `entity_update("subagents", ...)` 在 payload 里挂
  `_transition_reason` / `_transition_actor`，业务 `PATCH /internal/entities/subagents/{id}`
  自动转路由到 `transition()`。
- PR-31 把转移历史落到持久 `subagent_state_transitions` 表；PR-31c（2026-04-15）
  进一步删除了进程内 `_transitions` Counter（曾经存在于
  `business.internal.subagent_state` 和 `novaic_cortex.scope_state`）。想拿到
  transition 计数/速率的话，不再有 `dump_transition_counters()`——直接查表：
  `sqlite3 ~/.novaic/data/entangled.db "SELECT from_state, to_state, reason,
  COUNT(*) FROM subagent_state_transitions GROUP BY 1,2,3"`，或者走
  `GET /v1/state_transitions/subagent/<id>?limit=N` 单实体回放。

## Cortex Scope 状态异常查因（PR-29 state machine，2026-04-15）

Cortex 的 scope 生命周期写入只有一条合法路径：
`novaic_cortex.scope_state.transition(...)`（`workspace.complete_child_scope` /
`workspace.archive_root_scope` / `workspace.create_scope` 都已迁过去）。
每次合法转移会留下两行：

```
scope_state scope=<scope_path> <from_phase> -> <to_phase> reason=<r> actor=<a>
[CORTEX] scope.state_transition scope_path=... from_state=... to_state=... reason=... actor=...
```

常见问题定位：

```bash
cd /opt/novaic/data/logs

# 1. 某 scope 完整生命周期（创建 → 归档）
rg "scope_state scope=/ro/active/<scope_id>" cortex-*.log

# 2. 试图复活终态 scope（违反 INV-6）
rg "InvalidScopeTransition|archived -> executing" cortex-*.log

# 3. 重复 scope_end 是否被 idempotent self-loop 吞了（应见 noop=True）
rg "scope_state scope=/ro/scopes/<scope_id> archived -> archived" cortex-*.log
# 没结果是预期 —— self-loop 不会写日志/不 bump metric，只刷新 ended_at
```

### 常见信号

| 现象 | 解读 |
|------|------|
| `reason=scope_end_root actor=cortex.workspace` | 用户主动 wake/interrupt 触发的根 scope 归档；正常 |
| `reason=scope_end_child actor=cortex.workspace` | skill_end 关闭的子 scope；正常 |
| `InvalidScopeTransition: archived -> executing` | 调用方在试图复活已归档 scope —— 一定是 bug，定位 caller |
| `complete_child_scope` 的日志只有 `scope.child_completed` 没有 `scope_state` | 走了直写 `meta["phase"]` 旁路 —— `scripts/ci/lint_scope_phase.sh` 应该提前拦下 |

### 原理

- `scope_state.py` 的 `ALLOWED` 矩阵：`EXECUTING` 可去 `COMPACTING/ARCHIVED/FAILED`；`ARCHIVED`/`FAILED` 出度为 0（终态）。
- INV-5（scope_end 幂等）由 `transition()` 内的 `current == to` 自环实现：noop 不 bump metric，但仍允许 `extra` 写入（让重试刷新 `ended_at`）。
- INV-6（archival 方向性）由 `ARCHIVED` 出度为空集结构性保证，根本不可能写出 `archived -> executing`。
- `scripts/ci/lint_scope_phase.sh` 禁止任何文件直写 `meta["phase"]` 或 dict 字面量 `"phase": "archived"`，强制走 `transition()`。

## chat_messages legacy 列在生产 DB 残留（PR-30，2026-04-15）

PR-30 合并后首次启动 Entangled 时，`ensure_schema` 会一次性：
1. 跑 `backfill_lifecycle`（把 `processed=1 → consumed`、`claimed_by 非空 → claimed`）。
2. 跑 `drop_legacy_message_columns`（`ALTER TABLE chat_messages DROP COLUMN {processed,claimed_by,claimed_at,status}`）。

如果观察到：

```bash
sqlite3 /opt/novaic/data/entangled.db "PRAGMA table_info(chat_messages);" \
  | awk -F'|' '{print $2}'
```

输出里还能看到四个 legacy 列之一，说明 `ensure_schema` 那条路径出问题了。排查：

```bash
# 1. Entangled 日志里应该看到这两条（首次启动）或 0 rows（之后）
rg "backfill_lifecycle migrated" /opt/novaic/data/logs/entangled-*.log
rg "drop_legacy_message_columns dropped" /opt/novaic/data/logs/entangled-*.log

# 2. 没看到 → ensure_schema hook 没触发，多半是 MESSAGES_DEF 没带 lifecycle 字段
rg "'lifecycle'" /opt/novaic/services/novaic-business/business/schema_push.py

# 3. 或者 sqlite 版本 < 3.35 不支持 DROP COLUMN
sqlite3 --version  # 需要 ≥ 3.35.0
```

手动补做（**先备份 DB**）：

```bash
cp /opt/novaic/data/entangled.db /opt/novaic/data/entangled.db.pr30.bak
sqlite3 /opt/novaic/data/entangled.db <<'SQL'
UPDATE chat_messages
   SET lifecycle = CASE WHEN processed=1 THEN 'consumed'
                        WHEN claimed_by IS NOT NULL THEN 'claimed'
                        ELSE lifecycle END,
       claimed_by_scope = COALESCE(claimed_by_scope, claimed_by),
       lifecycle_updated_at = COALESCE(lifecycle_updated_at, strftime('%s','now')*1000)
 WHERE lifecycle='pending' AND (processed=1 OR claimed_by IS NOT NULL);
ALTER TABLE chat_messages DROP COLUMN processed;
ALTER TABLE chat_messages DROP COLUMN claimed_by;
ALTER TABLE chat_messages DROP COLUMN claimed_at;
ALTER TABLE chat_messages DROP COLUMN status;
SQL
```

注意：**`read` 列不删**，它承载 UI 侧未读回执语义。

## 消息没回复的 SOP（PR-25 trace，2026-04-15）

第一步不是 grep 日志，是 curl trace。端点把 chat_messages + message_outbox
+ Cortex scope meta 拉到一个响应里，节省四次 sqlite / 四份日志的翻阅。

```bash
MID="<message_id>"
SVC="$(awk -F'= ' '/^service_token|^jwt_secret/{print $2; exit}' \
        /opt/novaic/etc/services.toml 2>/dev/null)"

curl -s -H "X-Service-Token: $SVC" \
     -H "X-Internal-Service: ops" \
     http://localhost:19998/internal/messages/$MID/trace | jq .
```

读返回的优先级：

1. `lifecycle` —— `pending` 说明 subscriber 还没 claim；`claimed` 说明进了 scope
   但 scope 尚未 end；`consumed` 正常；`orphaned` 看 `outbox.last_error`。
2. `outbox.last_error` —— subscriber 最近一次失败原因（非空即需处理）。
3. `outbox.delivered_at` 非空但 `lifecycle=pending` —— PR-22 wiring bug，
   subscriber dispatched 成功但忘了 transition。对着 dispatch_subscriber.log
   grep `message_id`。
4. `scope.input_message_ids` —— 消息进了哪个 scope、同批还有谁。
5. `errors[]` —— 如果有 `cortex: ...`，说明 Cortex 那半边读失败（trace 主干
   仍可信），回去看 cortex.log。

404 → 消息 id 根本不存在（typo / entity 未落盘）。
502 → Entangled 起不来，先处理 Entangled。

## 按 state-transition history 回放实体生命周期（PR-31，2026-04-15）

PR-21/28/29 把 message/subagent/scope 的状态都收敛到了 `transition()`
唯一入口，PR-31 把这些转移事件落到持久表里。要回答 "这个实体为什么还在
\<某状态\>？" 不再靠翻日志，直接查历史表。

### 三条查询入口

```bash
# A. 一条消息的生命周期（等价于 grep "message_state <id>" 但更整齐）
curl -s -H "X-Service-Token: $SVC" \
  http://biz/internal/messages/<message_id>/trace | jq '.history'
# 或直接看原始表：
curl -s -H "X-Service-Token: $SVC" \
  http://entangled/v1/state_transitions/message/<message_id>

# B. 一个 subagent 的状态机轨迹（和 /history 区分：那个是 chat 上下文）
curl -s -H "X-Service-Token: $SVC" \
  http://biz/internal/subagents/<agent_id>/<subagent_id>/state-history

# C. 一个 scope 的阶段流转（NDJSON 日志，按 scope_path 过滤）
curl -s -H "X-Internal-Key: $CORTEX_KEY" \
  "http://cortex/v1/scope/history?scope_path=/ro/active/<scope_id>"
```

### 幂等不写日志的含义

- 订阅者重投、recovery 重跑触发的 A→A 是 **noop**，history 表不记录。
  所以 "claimed 状态但只看到一条 claimed 转移" 是对的，不是 bug。
- 反过来，如果看到 history 为空但 `subagents.status` 不是初始值
  （`sleeping`），说明转移发生在 PR-31 之前 — 查部署时间线，不要当事故。

### 日志 vs 历史表的分工

| 来源 | 用途 | 何时看 |
| --- | --- | --- |
| 日志 `rg "message_state <id>"` | 带时间戳、带 pid、跨服务 correlate | 要拼 Cortex/Queue/Worker 一起看时 |
| `*_state_transitions` 表 | 纯状态机视图，oldest-first | 只关心 "这个 id 走了哪些状态" |

### 表和文件在哪

```bash
sqlite3 ~/.novaic/data/entangled.db ".schema message_state_transitions"
sqlite3 ~/.novaic/data/entangled.db ".schema subagent_state_transitions"
# Scope 侧是 NDJSON：
cat ~/.novaic/cortex/scope_state_transitions.ndjson | jq
# 或按 CORTEX_SCOPE_STATE_LOG 覆盖过的路径。
```

### 出问题怎么恢复

- **Entangled 写 history 行失败（message）**：co-transactional，写失败会让
  UPDATE 一起回滚 — 日志里会看到 `sqlite3.OperationalError` 堆栈。
- **Entangled 写 history 行失败（subagent，PR-31b 之后）**：同样 co-transactional
  —— 2026-04-15 之后 subagent 侧已从 best-effort POST 升级成 server-side
  `transaction("global")` 原子提交。若 INSERT 失败，整个 transition 会 raise
  HTTP 500，Business 的 client 会把它翻译成 `EntangledClientError` 冒泡出去，
  调用方（subscriber / recovery_worker）会走各自的重试路径。换句话说：
  **PR-31b 之后再也不会出现 "subagent.status 提交成功但 history 少一条" 的场景**。
- **Cortex NDJSON 盘满**：`append_transition` 抛 `OSError`，WARN 一行
  `scope_state append_transition FAILED (continuing): ...`，`meta.phase`
  仍然被更新。清盘后重启 Cortex 即可，不需要补写历史。

### PR-31b 新增：subagent 状态机独立查询入口

`GET /v1/subagents/states` 直接返回 Entangled 内部的 `ALLOWED_TRANSITIONS` 矩阵，
用来在运维时自问 "从 `failed` 能到哪里？"（答：只能 `sleeping` 或 `awake`，
不能直接 `running`）：

```bash
curl -s -H "X-Service-Token: $SVC" http://entangled/v1/subagents/states | jq
# {"states": [...], "allowed": {"sleeping": ["awake","running",...], ...}}
```

如果业务方对 transition 结果有疑问，直接去打同一个矩阵服务器的响应，避免
Business 侧 `ALLOWED` 文案飘移（PR-31b 之后 Business 的矩阵只是 informational
副本，规则以 Entangled 返回的为准）。

### 陷阱：嵌套 `transaction("global")` 必 hang

PR-31b 在 prod smoke 时踩过：`append_subagent_transition` 原来自己开事务，配合
PR-31b 的外层 `subagent_state.transition` 形成嵌套写锁——SQLite 在同一连接上
会"看似可重入"但对第二次 global lock 等待索的释放，端到端表现成 curl 15s 超时
零日志。修复把 helper 改成 transaction-agnostic（参照 `append_message_transition`），
规则：**任何 `append_*_transition` helper 不自己开事务，遗留的纯 HTTP shim
自己 wrap**。今后新增同类 helper 务必照此模式，否则 smoke 会挂，单测的
`FakeDatabase` 又不锁不会暴露。

## Subscriber 每次 deploy 后回到 disabled（TD-5，2026-04-15 根治）

**症状**：运维在生产跑 `deploy-business.sh` 之后，日志里重新出现
`Subscriber: disabled (runtime_switches.subscriber_enabled=False)`，message_outbox
停止 drain。手动改 `services.json` 三个拷贝（novaic-common / novaic-gateway /
novaic-agent-runtime）→ restart 能救活，但下一次 deploy 再次复发。

**根因**：`rsync -azL --delete` 把 committed `services.json` 覆盖回
`subscriber_enabled: false`。修复前 `runtime_switches` 和代码默认值住在同一文件。

**根治后的正确姿势**（PR-33 §C.2.2 TD-5）：只编辑
`/opt/novaic/etc/runtime_switches.json`，位置在 `/opt/novaic/services` 之外，
rsync 物理碰不到。`common/strict_config.py` 在 load 时 deep-merge 这个 overlay。

```bash
ssh root@api.gradievo.com
cat /opt/novaic/etc/runtime_switches.json
# {
#   "subscriber_enabled": false,
#   ...
# }

# 开 canary：
cat > /opt/novaic/etc/runtime_switches.json <<'JSON'
{
  "subscriber_enabled": true,
  "health_check_interval_seconds": 5,
  "scheduler_poll_interval_seconds": 1.0,
  "fallback_max_per_tick": 50
}
JSON
bash /opt/novaic/start.sh --stop && bash /opt/novaic/start.sh

# 确认生效：
grep 'runtime_switches=' /opt/novaic/data/logs/business-$(date +%Y%m%d).log | head -1
# → subscriber_enabled=true
```

**不要**再去编辑 `/opt/novaic/services/novaic-common/config/services.json`（或
它的 novaic-gateway / novaic-agent-runtime 兄弟拷贝）—— overlay 会盖住你的改动，
且下一次 deploy 会用 rsync 把文件回滚到 committed 版本。Overlay 里的 key 必须
和 committed `services.json` 的 `runtime_switches` 段里声明过的 key 完全对齐；
typo 会在启动时 `ConfigError: unknown key(s) [...]` 硬 fail，这是有意的 —
静默 no-op 才是 TD-5 要消灭的失败模式。

**首次部署**：`deploy-business.sh` 跑完会自动种子化
`/opt/novaic/etc/runtime_switches.json`（从 committed defaults），
已存在则保留 operator-owned 内容。

## LLM 调用失败排查

1. 日志：`grep -E "429|think.*failed" /opt/novaic/data/logs/task-worker-*.log`
2. Context：从 **`tq_sagas.step_results`** 等与 `read_context` 相关字段取（**不要**误用 `runtime.context`）
3. 重放：`POST /api/queue/tasks/publish` topic=`llm.call`
4. 脚本：`novaic-agent-runtime/scripts/trace_llm_call.py`（若存在）

## 相关

- [../architecture/entangled-store-and-app-ws.md](../architecture/entangled-store-and-app-ws.md) — AppWS / store  
- [../reference/config-and-environment.md](../reference/config-and-environment.md)  
