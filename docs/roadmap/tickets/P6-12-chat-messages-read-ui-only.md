# P6-12 — `chat_messages.read` 降级为 UI-only 字段

> Historical ticket archive: this closed ticket predates the Environment
> notification cutover. Any `chat_messages.lifecycle` or message lifecycle
> wording here is archaeology, not current architecture.

| Field | Value |
|---|---|
| **Ticket**  | P6-12 |
| **Status**  | `[✓]` contract landed 2026-04-24（docs + CI 承诺；代码survivors 已 inventory 并贴弃用注释） |
| **Opened**  | 2026-04-24 |
| **Owner**   | wc |
| **Blocks**  | (none — 文档收官票) |
| **Blocked by** | PR-46 (deployed), P6-11 (R10 写入承诺表) |
| **Invariant** | R10 — runtime / subscriber / HealthWorker / Assembler 的**读取与写入**都不得再把 `chat_messages.read` 当作业务语义；`read` 只服务 UI 未读气泡 |

---

## 目的

P6-11 把 **R10 (Consumer SSOT)** 正式写进 `docs/architecture/message-wake-principles.md`。本票把 R10 的"字段层细则"落地到：

1. **审计**——列出仓库里所有仍在读/写 `chat_messages.read` 的代码位点。
2. **承诺**——逐条写清：*该位点是彻底移除、弃用、还是 UI-compat 保留*。
3. **CI**——加一条 grep 规则，禁止**新增**的 runtime/subscriber/assembler/healthworker 代码读 `chat_messages.read`（已落的 survivors 通过 allowlist 放行）。

P6-12 **不改运行时行为**（PR-46 早已把 runtime 的 read 读取从主路径下线了）；它是**契约收官**：让"UI-only"从一句文档口号变成 grep 可查的硬约束。

---

## 一、审计：当前所有 `chat_messages.read` 触点

### A. Runtime（`novaic-agent-runtime/task_queue/handlers/context_handlers.py`）

| 位点 | 行为 | R10 判定 | 处置 |
| --- | --- | --- | --- |
| `_fetch_replay_rows` 的 `"read": "1"` 过滤器 | 拉 "已读" 消息做 `<CHAT_HISTORY>` 回放 | **survivor**：语义是"已消费"而非"UI 已读"，但当前 proxy 碰巧重合 | **[FOLLOW-UP]** 下一个补丁把 filter 迁移到 `lifecycle='consumed'`（entity_list 支持后）；本票先贴 `# R10-survivor` 注释 |
| `handle_context_read` merge 成功后 `{"read": 1}` 写入（2 处） | 把刚被 agent 读进 context.jsonl 的消息标 UI 已读 | **UI-compat write-through**：UI 依赖 `read` 字段刷新红点；runtime 作为"first reader" 代为 flip | **保留**，注释升级到明文"UI-compat"；真正权威的"消费完成"由 PR-22 `message_state.transition("consumed")` 在 scope_end 负责 |
| Legacy fallback 的 `"read": "0"` 扫描（`CONTEXT_READ_BY_IDS=0` 分支） | PR-46 kill switch 回退路径 | **kill switch only**，默认 off | **保留 kill switch**；PR-46 cut-over 成熟一个 release 后整段删除（独立 PR 管理） |

### B. Business internal API（`novaic-business/business/internal/message.py`）

| 位点 | 行为 | R10 判定 | 处置 |
| --- | --- | --- | --- |
| `_store_add_message` 默认 `"read": 0` | 新消息初始 UI 未读 | **合规**（UI 字段默认值由写入路径设置） | 保留 |
| `GET /internal/chat/history` 返回 `read` 字段 | UI 渲染 | **合规**（UI-facing） | 保留 |
| `POST /internal/chat/clear` 批量 `{"read": 1}` | "全标已读"按钮 | **合规**（UI-facing） | 保留 |
| `GET /internal/messages/unread/{agent_id}` | filter `read=0 & type=USER_MESSAGE` | **僵尸路由**：当前代码库无 Python caller（仅文档引用） | **[DEPRECATE]** 贴弃用注释 + 在 docstring 顶部写 "R10: no internal callers as of 2026-04-24; scheduled for removal after two releases without hit"；监控一个 release 后整段删除（独立 PR） |
| `GET /internal/messages/unread-sent/{agent_id}` | 同上，含 SYSTEM_WAKE/SUBAGENT_* | **僵尸路由** | **[DEPRECATE]** 同上 |
| `GET /internal/messages/unread-count/{agent_id}` | 未读计数 | **僵尸路由**（Monitor 侧当前不调；文档遗物） | **[DEPRECATE]** 同上 |
| `GET /internal/messages/unread-grouped` | HealthWorker 旧兜底扫描源 | **僵尸路由**（PR-19 已废除此扫描路径；历史上"唯一唤醒路径" hihi 事件的罪魁） | **[DEPRECATE]** 同上 |

### C. Entangled / Queue Service / Cortex / Assembler

- **Entangled**：`chat_messages.read` 是 schema 字段之一，持久化由 entity_store 按 row 透传；Entangled 自身**不消费**它（R10 合规）。
- **Queue Service**：无引用。
- **Cortex**：无引用。
- **Assembler / DispatchSubscriber**：无引用（PR-46 后 DispatchSubscriber 看的是 `chat_messages.lifecycle` + outbox，完全绕开 `read`）。
- **HealthWorker**：无引用（PR-19 以来 scanner 走 `lifecycle='pending'` → PR-51 Part 2 加 stuck-claimed 扫描；全程不碰 `read`）。

### D. 测试

| 位点 | 处置 |
| --- | --- |
| `novaic-agent-runtime/tests/test_pr50_chat_history_byte_cap.py` ("read": 1 fixture) | 保留（fixture 模拟 DB 行，不代表 runtime 读 `read`） |
| `tests/test_wake_im_replay.py` / `test_context_read_by_ids.py` 的 assertion | 保留（断言 runtime 正确地按 PR-46 行为走） |

---

## 二、CI 硬约束

新增 `scripts/ci/lint_chat_messages_read.sh`：

```bash
# 禁止非 allowlist 的代码在 runtime/subscriber/assembler/healthworker 中
# 读 chat_messages.read。匹配形态：
#   "read": 0|1           (dict literal / JSON)
#   read=0|1              (kwargs)
#   WHERE read = 0|1      (SQL)
#   filter(read=          (ORM-ish)
# allowlist: UI-compat 写入位点（context_handlers 已贴注释）
```

`scripts/ci/run-linters.sh` 串进。命中未 allowlist 位点 → exit 1。

---

## 三、文档落点

- [x] `docs/architecture/message-wake-principles.md` §二、R10 条 + §三 详述 + §六 事故复盘（P6-11）
- [x] 本票（P6-12）作为"字段级收官审计"的 SSOT
- [x] `docs/roadmap/message-wake-refactor.md` P6-12 行勾选
- [x] `docs/roadmap/tickets/README.md` 索引加一行

---

## 四、验收

- [x] 仓库中 `chat_messages.read` 的所有读/写位点**都被本票审计表覆盖**（grep 交叉验证零遗漏）
- [x] Runtime 代码的两类 survivor（replay filter / UI-compat write）都有就地注释引用本票 + R10
- [x] 4 个 Business 僵尸路由都贴了 `# [R10 DEPRECATED]` docstring 标记 + sunset 计划
- [x] `scripts/ci/lint_chat_messages_read.sh` 落地并接入 `run-linters.sh`

---

## 五、后续（不在本票）

- **[FOLLOW-UP-1]** Runtime `_fetch_replay_rows` 迁移到 `lifecycle='consumed'` filter（需要 Entangled `entity_list` 支持 `lifecycle` 参数；参考 PR-21/PR-46 的 params 扩展做法）。
- **[FOLLOW-UP-2]** 观察一个 release 后删除 4 个僵尸 `/messages/unread*` Business 路由（`git log --grep "unread-grouped"` 零 prod hit 作为删除前置）。
- **[FOLLOW-UP-3]** 观察一个 release 后删除 `context_handlers.py` 的 legacy fallback 分支 + `CONTEXT_READ_BY_IDS` kill switch。
- **[FOLLOW-UP-4]** UI 长期目标：不再读 `chat_messages.read`，改读 `lifecycle != 'consumed'` + 本地 dismissal 状态；届时 runtime 的两处 `{"read": 1}` write-through 可彻底删除。
