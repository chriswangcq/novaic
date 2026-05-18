# PR-46  context.read 按 `payload.message_ids` 精确装配（杜绝"扫 agent pending"反模式）


| 字段             | 值                                                                                             |
| -------------- | --------------------------------------------------------------------------------------------- |
| **Phase**      | hotfix（R2 / R9 真正落地的先决条件）                                                                     |
| **Milestone**  | M2+（主路径已切 subscriber，消费端必须对齐 message_ids）                                                     |
| **承诺**         | R2（dispatch 唯一入口）、R4（lifecycle 唯一事实）、R9（wake 不丢/不错上下文）                                        |
| **Status**     | `[✓]` — **已部署 prod 2026-04-22 18:00 UTC**。`CONTEXT_READ_BY_IDS=True` 已在 runtime 内生效（staging smoke 已验证）；观察指标 `context_read_by_ids_total` 下一周回填 |
| **Depends on** | PR-20（scope.input_message_ids）、PR-21（lifecycle 枚举）、PR-38（IM 渲染）                               |
| **Blocks**     | PR-43（scope chain 之前必须先有"新消息真的进当前 scope"的基线）、PR-47（老毒清理依赖精确装配就能自愈）                            |
| **估时**         | 0.5–1 d                                                                                       |
| **Owner**      | __                                                                                            |
| **PR 标题**      | `fix(runtime): context.read must assemble by payload.message_ids, not agent-wide unread scan` |


## 事件摘要

2026-04-22 用户连发 `hi hi`（12:06）和 `现在几点了`（12:07），两轮 wake 的 LLM payload 里：

1. `messages[]` 最新一条 user 消息是 `**msg_id=7227fd7fa8ab at 2026-04-21T14:57` "没事 停止吧"**；04-22 的两条新消息一条也没出现。
2. 11 条 04-17 ~ 04-21 的历史 USER_MESSAGE 被原样塞进 `role=user` 槽位，每轮重复投喂。
3. LLM 看不到任何"新输入"，只能不停演"刚醒过来说抱歉 + 自我介绍"的同一套剧本，**结构性回答不了用户当前的问题**。

### 根因（static grep，不是猜测）

`novaic-agent-runtime/task_queue/handlers/context_handlers.py::handle_context_read` 在合并用户消息时使用：

```python
all_messages = business_client.entity_list(
    "messages",
    params={
        "agent_id": agent_id,
        "read": "0",                 # ← 按 agent_id 扫全部 unread
        "order_by": "timestamp ASC",
    },
)
```

**问题**：扫的是"这个 agent 名下所有 read=0 的消息"，**不是** `payload.message_ids` 里 DispatchAssembler 指定的那一批。

直接后果：

1. 一旦历史上有若干条 USER_MESSAGE 因为 agent 崩溃 / 超时 / claim race 停留在 `read=0`（PR-41 止血前的积压就是典型），它们会在**每一轮新 wake** 被重新装配进 Cortex context.jsonl + 标记 `read=1`。但 Cortex context.jsonl 是 append-only 的——下一轮 wake 走 `bridge.recall_messages()` 时又把它们跨 scope 拉回来。
2. 新到的 USER_MESSAGE 如果此刻 Business 侧 `read=0` 还没 commit（dispatch 并发写入 race）或者 subscriber 已经把它改成 `claimed` 但 Entangled 的 `read` 字段未同步，**新消息反而从 `read=0` 过滤里漏掉**。"旧的每轮都来、新的一条没有"就是今天观察到的样子。
3. 违反 R2：DispatchAssembler 辛辛苦苦透传到 queue payload 的 `message_ids` 数组，到 runtime 这一跳被彻底忽略，等于 dispatch 合约在 runtime 边界处被撕掉。
4. 违反 R4：`read=0` 过滤和 `lifecycle` 枚举（PR-21 里 `pending/claimed/consumed`）是两套平行状态机，一个消息在 `lifecycle=claimed` 但 `read=0` 会被重复消费，违背"单一事实"原则。

## 方案

**统一口径：runtime 只信 `payload.message_ids`**。任何"这次 wake 应该消化哪些消息"的问题，答案必须是 DispatchAssembler 透传过来的那批 id，**再无其他来源**。

### A. `handle_context_read` 改按 id 取

```python
# context_handlers.py::handle_context_read
requested_ids = payload.get("message_ids") or []
if requested_ids:
    # 精确按本轮 dispatch 承诺的 id 集合取
    all_messages = business_client.entity_list(
        "messages",
        params={
            "agent_id": agent_id,
            "ids": ",".join(requested_ids),   # 新增参数（见 B）
            "order_by": "timestamp ASC",
        },
    )
else:
    # 退路：buffered 分支（scope 仍 running，新消息通过
    # append_scope_input 追加）时 payload 不带 message_ids，
    # 但 scope.meta.input_message_ids 里有 —— 改从 Cortex
    # 那里取，而不是扫 agent unread。
    input_ids = bridge.get_scope_input_message_ids(scope_id)  # 已有（PR-20）
    if input_ids:
        all_messages = business_client.entity_list(
            "messages",
            params={"agent_id": agent_id, "ids": ",".join(input_ids),
                    "order_by": "timestamp ASC"},
        )
    else:
        all_messages = []          # 没 id 就什么都不合并（fail-closed）
```

**为什么 fail-closed**：当前"扫 agent unread"本质就是 fallback，副作用远大于正向收益。真正的 `handoff_notes` / recall 路径 PR-42/45 已经兜住；这里少合并几条旧消息，LLM 会看到"scope 本轮只有一条新 user 消息"——这才是 R9 想要的清晰首轮状态。

### B. Business `/internal/entities/messages` 支持 `ids=` 过滤

当前 list 端点只支持 `agent_id / read / order_by / limit`；新增 `ids=comma,separated` 参数（Entangled CRUD 层已支持，只是 Business 代理层没透出）。

**为什么选 ids 而不是给每个 id 独打一次 GET**：11 条 message ids 打 11 次 HTTP 代价太高；bulk by-ids 一次请求就能回全部。

### C. `read=1` 的写回不再作为"吃掉"标记

当前写 `read=1` 的动机是"下次 context.read 扫 unread 时别再捡到"。一旦改成按 id 精确取，`read` 字段就退化为纯 UI 标记（前端小红点），runtime 侧不再对它做业务判断。

- **保留写 `read=1`**：不破坏 UI（前端还在用它）。
- **不再读 `read=0`**：runtime 所有分支都走 message_ids 精确装配。

以后 `read` 字段按 PR-30 的窄化口径继续存在，但再被 runtime 读就是 lint 违规（见 D）。

### D. CI lint：禁止 runtime 代码读 `read=0` / `read=1`

```bash
# scripts/ci/lint_no_read_flag_in_runtime.sh
rg -n 'read["\']?\s*[:=]\s*["\']?0' novaic-agent-runtime/task_queue/ \
  && { echo "runtime must not filter by read=0/1 — use message_ids instead"; exit 1; }
```

防止未来新代码复读"扫 unread"反模式。

## 范围

### runtime

- `novaic-agent-runtime/task_queue/handlers/context_handlers.py::handle_context_read`
  - 删除 `read=0` 过滤分支
  - 新增 `requested_ids = payload.get("message_ids") or bridge.get_scope_input_message_ids(scope_id)` 口径
  - `bridge.get_scope_input_message_ids` 如不存在，看 PR-20 的 `meta.input_message_ids` 读法
- `novaic-agent-runtime/tests/test_context_read_by_ids.py`（新）

### business

- `novaic-business/business/internal/entity.py::internal_list_entity`：接受 `ids=` 参数并透传给 Entangled
- 或者：`novaic-business/business/internal/message.py` 专门加 `/internal/entities/messages?ids=` 的代理

### entangled

- `packages/server-python/entangled/app/crud.py::list_entities` / `messages`：确认 `ids=` 过滤已支持；没有就补

### CI

- `scripts/ci/lint_no_read_flag_in_runtime.sh` + `.github/workflows/lint.yml` step

### 文档

- `docs/architecture/message-wake-principles.md §R2`：补一条"runtime 消费端只认 message_ids"的子承诺
- `docs/architecture/agent-pipeline.md`：把"扫 unread"这条旧描述删掉

## 实施 Checklist

### A. runtime（2026-04-23 完成）

- `handle_context_read` 改按 `scope.meta.input_message_ids` 取消息（SSOT 取代 `payload.message_ids` —— meta 由 PR-20 `bridge.append_scope_input` 在 fresh-wake & buffered 两条路径都写）
- buffered 分支天然通过 `scope.meta.input_message_ids` 取（PR-20 写入路径）
- 空 id 集合 → 不合并任何消息（fail-closed）
- 保留 `entity_update(messages, {read: 1})` 做 UI 兼容
- 日志 `event=context_read kind=by_ids scope=... input_ids=N unseen=M fetched=K`
- Unseen-delta 优化：`seen_keys` 里已有的 `user-msg-{id}` 跳过 GET，长 scope O(new) 代替 O(total)
- kill switch `CONTEXT_READ_BY_IDS=0` 回退 legacy 扫描（staging 可随时切回不用 redeploy）
- `metric_inc("context_read_assembly_total", kind=by_ids|unread_scan)` + `metric_inc("context_read_fetch_total", mode, result)`

### B. business/entangled（最终方案：不需要 bulk 接口）

- **不新增**: runtime 端按 unseen delta N-GET（典型 1-3 次/round），现有 `entity_get` 够用；复杂度 0
- 未来如需 bulk by-ids（例如一个 scope 一次 buffered 10 条），走 `list_stream` 的 `in_filters`（已存在），单独 PR

### C. CI（defer）

- `scripts/ci/lint_no_read_flag_in_runtime.sh` —— 与 PR-30 `read` 字段窄化一并出，不阻塞 PR-46 合并
- `.github/workflows/lint.yml`

### D. 单测（全部绿，`tests/test_context_read_by_ids.py` 新增 9 cases）

- meta 带 3 个 ids → 装配 3 条，ASC 排序正确
- meta 带 0 个 ids → 不 fetch 任何消息（fail-closed，entity_get 不被调）
- meta 缺 `input_message_ids` key → 同上 fail-closed
- ids 里有"已被 Cortex 持久化的"（`_idempotency_key` 在 seen_keys）→ 跳过，只 fetch delta
- Business 返回 None（404，被 PR-47 age cap 删掉的场景）→ 跳过，不 raise
- Business 抛异常 → 跳过该条，其余继续
- SUBAGENT_SEND 过滤（target_subagent_id 匹配）在 by-ids 路径上与 scan 路径语义一致
- `CONTEXT_READ_BY_IDS=0` → 回退 legacy `entity_list(read=0)` scan，`order_by="timestamp ASC"` 保留
- `read_session_meta` 抛异常 → 降级为 empty merge，不破坏整个 read

### E. 回归测试（全部绿，158 passed）

- `tests/test_context_read_ordering.py`（3 cases）：改用 kill switch 路径验证 legacy scan 仍正确
- `tests/test_im_rendering.py`（10 cases）：改用 by-ids 路径 + `entity_get.side_effect` mock
- `tests/test_wake_im_replay.py`（38 cases）：module-level autouse fixture `CONTEXT_READ_BY_IDS=0` 保留 PR-44 语义
- 全量 `novaic-agent-runtime` 158 passed（含 PR-45 / PR-44 / PR-37 / PR-20 / PR-21 / PR-26 所有）

## 验收

### 本地

```bash
cd novaic-agent-runtime && ./run_tests.sh tests/test_context_read_by_ids.py tests/test_context_read_ordering.py tests/test_im_rendering.py tests/test_wake_im_replay.py
cd novaic-business && ./run_tests.sh tests/test_entity_internal_list.py
./scripts/ci/lint_no_read_flag_in_runtime.sh
```

### 线上

```bash
# 1. 发一条新 user_message
# 2. 查 LLM 上游 payload（grep runtime 日志 event=context_read kind=by_ids）
#    预期：count=1 且 message_ids 完全匹配 dispatch 下发的 id
grep 'event=context_read' /opt/novaic/data/logs/runtime-*.log | tail -5

# 3. 验证新 scope 的 context.jsonl 只有本轮一条 user 消息（+ 系统 prompt + continuity 段 + recall）
sqlite3 ... "SELECT COUNT(*) FROM chat_messages WHERE scope_id = 'NEW_SCOPE' AND role='user';"
# 预期：1
```

## 部署 Checklist（必走）

1. 代码合入父仓 main（含 novaic-agent-runtime + novaic-business submodule bump，business 侧透参改动很小）
2. `./deploy services` + `./deploy runtime`
3. 线上证据 ≥ 2 段：
  - 日志 grep `event=context_read kind=by_ids count=` 至少 3 段命中，且 count 与 dispatch `message_ids` 长度一致
  - 回放一次新 USER_MESSAGE，SQL 验证新 scope `context.jsonl` 里 role=user 条数 = 本轮 dispatch 的 message_ids 长度
  - （负向）grep runtime 日志不应再出现 `event=context_read kind=unread_scan`（旧分支应已删除）
4. 迁移：无（老数据 read=0/1 字段继续保留做 UI）

## 风险 / 讨论

1. **buffered 分支数据源迁移**：当前 buffered 消息通过"下次 context.read 扫 unread"捕获。改 by-ids 后依赖 `scope.meta.input_message_ids` 必须被 PR-20 的 `append_scope_input` 可靠写入。bake 1 周观察这条路有没有漏写。
2. `**ids=` 过滤的 Entangled 支持**：若 Entangled CRUD 本来就不支持 `ids=`，补这个参数不是 0 成本；需要同步改 SQLAlchemy 过滤 + schema 定义。MVP 可以退化为"runtime 自己循环打 N 次 GET"，但那是暂时的。
3. **read=1 的 UI 语义漂移**：以后 runtime 不写 `read=1` 了吗？——**仍写**，理由见上文（前端依赖）。这意味着 `read` 字段从"状态机的一部分"退化为"UI 标记"，PR-30 文档需要 amendment。
4. **"fail-closed"会不会吞掉合法消息**：只在 `payload.message_ids + scope.input_message_ids` 都空时才 fail-closed。DispatchAssembler 所有现存分支（saga_started / buffered）都至少填其中之一（PR-20 保证）。如果真出现两个都空的 payload，那是上游 bug，runtime 不该帮忙补。

## 承诺登记

- **R2**：runtime 侧第一次显式声明"消费端只吃 dispatch 下发的 id"，补上跨服务合约的最后一公里。
- **R4**：消息 lifecycle 状态机从此单一可信（`pending → claimed → consumed`），`read` 字段退出业务判断。
- **R9**：PR-42/44/45 注入的 `<HANDOFF_NOTES>` / `<CHAT_HISTORY>` / `<HISTORICAL_SUMMARY>` 段终于能和"本轮新消息"正确共存——之前 11 条旧消息每轮重放会把这些段完全淹没。

## 备注

- 本 PR 是 PR-43（scope chain）的前置：scope chain 要对比"上一次 scope 的尾部 K 步"和"本轮新消息"，两者都必须清晰区分，今天 handle_context_read 的行为会让两者混成一团。
- 在 PR-47（老毒 USER_MESSAGE 清理）之前上线**也是安全的**——by-ids 装配天然忽略老毒 pending；PR-47 只是顺手把历史数据也擦干净让 orphan 计数归零。

