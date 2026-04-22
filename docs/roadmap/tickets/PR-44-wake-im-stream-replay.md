# PR-44  Wake 首轮 IM 流回放（`chat_messages` 已读历史注入）

| 字段 | 值 |
| --- | --- |
| **Phase** | R9 增益（非阻塞） |
| **Milestone** | — |
| **承诺** | R9（PR-42/43 之补完）+ R4（IM 流可追溯） |
| **Status** | `[x]`（2026-04-21 实施） |
| **Depends on** | PR-42（wake continuity 注入点已存在）、PR-38（IM message rendering） |
| **Blocks** | — |
| **估时** | 0.5–1 d |
| **Owner** | wangchaoqun |
| **PR 标题** | `feat(runtime): replay last N chat_messages into first round context on wake` |

## 事件摘要

场景：agent sleep 期间，用户在 IM 里发了 3 条消息。agent 醒来后第一轮 `context.read`，按"未读指针"的语义只能看到这 3 条（或其中被 claim 触发的那条）；之前**已读**的历史消息（即 sleep 前的对话）完全看不到。

PR-42 解决了"agent 自己睡前的交接"，PR-43 解决了"前一个 scope 的工具轨迹"，本 PR 解决：

> "sleep 期间用户连发了好几句话，agent 醒来在 IM 流上下文里应当**一次性**看到'最近的对话'而不是'只看到有效触发那一条'"

以及更一般地：

> "苏醒后第一轮 think，应当看到最近 K 条 chat_messages 的完整文本（无论 read 指针），便于 LLM 判断话题是否延续。"

## 根因 / 现状

`handle_context_read`（`novaic-agent-runtime/task_queue/handlers/context_handlers.py`）的 merge 逻辑：

1. 读 Cortex 当前 scope 的 `context.jsonl`（system + tool steps）
2. 从 EntityStore 按 `last_read_ts` 之后 + 按 agent_id scope 查 `chat_messages`（未读）
3. merge 并按 timestamp ASC 排序，IM-rendering（PR-38）user-origin 消息
4. 返回给 LLM

"未读指针"对**同一 scope 内**连续 think 轮次是对的（每轮只要新增的消息）。但**苏醒首轮**它把"sleep 前已读的 chat_messages"也排除在外，因为 `last_read_ts` 已指向 sleep 前最后一条消息。

→ 新 scope 里只能看到 sleep 期间的未读消息，看不到 sleep 前的对话上下文。

## 方案

**仅在苏醒首轮（new scope 的第一次 context.read）**，把最近 K 条 `chat_messages`（不论 read 指针）**全部**渲染并前置注入。之后轮次保持现状（未读指针）。

### 1. 如何识别"苏醒首轮"

判据（任一即可）：

- a. `scope.meta.round_num == 0`（session.init 刚建好，第一次进入 think）
- b. scope.context.jsonl 的非 system_prompt / 非 WAKE_CONTINUITY / 非 PREV_SCOPE_TAIL 条目数 == 0
- c. 专门的 flag：session.init 写 `meta.wake_replay_pending=true`，首轮 context.read 消费后置 false

**选 c**（原子 + 可观测），session.init 阶段判断：

```python
# handle_session_init 结尾
if trigger_type in ("scheduled_wake","recovered","user_message","subagent_send"):
    bridge.update_session_meta(scope_id, wake_replay_pending=True)
```

`handle_context_read` 首次读到 `meta.wake_replay_pending=True`：
- 拉最近 K 条 chat_messages（不论 read 指针）
- 渲染并注入
- 置 `wake_replay_pending=False`（同事务 / 同次 meta write）

### 2. 选择最近 K 条的策略

```python
REPLAY_K = int(os.environ.get("WAKE_REPLAY_MESSAGE_COUNT", "20"))
REPLAY_MAX_AGE_SEC = int(os.environ.get("WAKE_REPLAY_MAX_AGE_SEC", "86400"))  # 24h
REPLAY_MAX_TOKENS = int(os.environ.get("WAKE_REPLAY_MAX_TOKENS", "6000"))

def _pick_replay_messages(agent_id, now_ts):
    rows = chat_messages_repo.list(
        agent_id=agent_id,
        types=("USER_MESSAGE","AGENT_REPLY"),  # 对话主流
        created_after=now_ts - REPLAY_MAX_AGE_SEC,
        order_by="timestamp DESC",
        limit=REPLAY_K,
    )
    rows = list(reversed(rows))  # 回到时间正序
    return _budget_trim(rows, max_tokens=REPLAY_MAX_TOKENS)
```

- `AGENT_REPLY` 也入选（否则 LLM 只看到用户的话不看到自己之前说的）
- 按 token 预算截断；截断时**保留最新**（丢最旧）
- 超过 `REPLAY_MAX_AGE_SEC` 的不回放（24h 前的对话已不相关，recall 兜底）

### 3. 渲染

- 每条 chat_messages 包装为 `{role: "system", content: f"<CHAT_HISTORY role={...} ts={...}>\n{content}\n</CHAT_HISTORY>", _message_type: "WAKE_IM_REPLAY"}`
- 用 system 而不是原生 user/assistant，避免 LLM 把它当"真实对话"误下 reply
- 插入位置：在 PR-42 的 WAKE_CONTINUITY 之后、当前 scope context 之前

### 4. 与 PR-42 / PR-43 的组合

注入顺序（新 scope 首轮 context）：

```
1. SYSTEM_PROMPT                         ← 已有
2. RECALL_MESSAGES (archived summaries)  ← 已有
3. WAKE_CONTINUITY (handoff + historical)← PR-42
4. PREV_SCOPE_TAIL (last K steps of X)   ← PR-43
5. WAKE_IM_REPLAY (last K chat_messages) ← 本 PR
6. 实际 context.read 拉到的"未读 chat_messages"（PR-38 IM-rendered）
```

互不覆盖、预算争抢时按优先级 compact（最先驱逐 5 > 4 > 3 > 2）。

## 范围

- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py::handle_session_init`（置 `wake_replay_pending` flag）
- `novaic-agent-runtime/task_queue/handlers/context_handlers.py::handle_context_read`（消费 flag + 回放）
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`（meta 读写 helper）
- 新增 env: `WAKE_REPLAY_MESSAGE_COUNT` / `WAKE_REPLAY_MAX_AGE_SEC` / `WAKE_REPLAY_MAX_TOKENS` / `WAKE_IM_REPLAY_ENABLED`

## 前置 Checklist

- [x] PR-42 已落地（WAKE_CONTINUITY 框架在）
- [x] PR-38 IM message rendering 已稳定
- [x] 与 PR-43 不冲突（注入点顺序已约定——PREV_SCOPE_TAIL 若上线放在 WAKE_IM_REPLAY 之前）

## 实施 Checklist

### 1. session.init 置 flag

- [x] `handle_session_init` 在 step 6 的 `update_session_meta` 里一次性写 `wake_replay_pending=bool(should_replay)`（同事务落盘，消除"scope 已建、flag 未写"的中间态）
- [x] 门控：`trigger_type in WAKE_IM_REPLAY_ENABLED_TRIGGERS` AND 无 caller-provided `initial_context`（sub-subagent bootstrap 路径不叠加）
- [x] `spawn_subagent` 写 `False`（而非不写），后续 `is True` 比较才严谨
- [x] 单测：eligible trigger 矩阵 / spawn 被屏蔽 / initial_context 被屏蔽 / 写的是字面 `bool` 非 `None`

### 2. context.read 消费 flag

- [x] `handle_context_read` 在 `read_context` 拿到持久 context 后、未读 merge 前：
  - [x] `bridge.read_session_meta(scope_id)`（软失败 → 视为 `{}`）
  - [x] `isinstance(meta, dict)` 防御（MagicMock / 非字典 meta 都降级为空，保护既有单测）
  - [x] `meta.get("wake_replay_pending") is True` 严格判定
  - [x] 若命中 → 调 `_build_wake_replay_block(...)` 生成消息 → `context.extend(...)` 追加（ephemeral，不写回 context.jsonl）
  - [x] log + metric（`wake_im_replay_total{result=injected|skipped_empty}` / `wake_im_replay_messages` histogram / `wake_im_replay_tokens` histogram）
  - [x] 清 flag：`bridge.update_session_meta(wake_replay_pending=False)`（失败只警告、不抛）
- [x] 未读增量逻辑未改，兼容 PR-36/PR-38 的 ASC + IM rendering
- [x] 单测覆盖：flag=True 注入 / flag=False 不注入 / 空历史也清 flag / Business 500 → 退化 / 清 flag 失败不崩 / 非字典 meta 不误触发 / read_session_meta 抛异常不误触发

### 3. 预算控制

- [x] `_pick_replay_messages` 每类型拉 `limit=K` → 按时间 `max_age_sec` 过滤 → 按 timestamp 合并排序 → 保留最新 K 条
- [x] `_budget_trim` 从**新**往**旧**累加 token 直到 `max_tokens`，丢最旧；输出仍按 ASC
- [x] token 估算用 `len(utf-8 bytes)//4` 低配启发式（热路径，+40 作 wrapper overhead）
- [x] 边界：0 条 / 空 business_client / K=0 / age=0 / 单条超限 / 全部超限

### 4. 与未读指针的去重（方案 B 实施）

- [x] 回放侧严格 `read=1`：只回放**已读过**的消息
- [x] 未读侧（existing code）严格 `read=0`：只拉未读
- [x] 两侧 SQL-equality 硬隔离，message-id 不会在两类消息里重叠出现，LLM 不会看到同一条消息的两种表示
- [x] 副作用：sleep 期间若恰好来消息，那条消息会走"未读"路径（user-role，参与 mark-read），历史回放不二次渲染；符合 PR-38 的 IM 语义

### 5. Feature flag

- [x] `WAKE_IM_REPLAY_ENABLED` 默认开启（`!= "0"` 视为开启，容错拼写）
- [x] 关停 = 短路：不读 meta、不调 Business、不改任何状态
- [x] 配套可调：`WAKE_REPLAY_MESSAGE_COUNT`（默认 20） / `WAKE_REPLAY_MAX_AGE_SEC`（默认 86400） / `WAKE_REPLAY_MAX_TOKENS`（默认 6000）——各自独立 `try/except ValueError` 容错回落
- [x] 单测：kill switch ON 时所有路径都被短路

## 测试 Checklist

- [x] 38 cases in `novaic-agent-runtime/tests/test_wake_im_replay.py`：
  - session.init flag 矩阵（eligible 矩阵、spawn 被屏蔽、initial_context 被屏蔽、literal bool）
  - helper 单测（`_estimate_tokens` / `_parse_ts_epoch` / `_budget_trim` 保新丢旧 / 边界）
  - `_pick_replay_messages` 路径（空 business、K=0、每类型 fan-out、类型级 500 软失败、age 过滤、type 合并 ASC、K 上限）
  - `handle_context_read` 集成（flag=True 注入 / flag=False 不注入 / kill switch 短路 / 排序 replay→unread / 空回放仍清 flag / Business 500 退化 / replay 不落盘 context.jsonl / 非字典 meta 防御 / meta 抛异常退化 / 清 flag 失败不崩）
- [x] 既有 48 个 `test_context_read_ordering` / `test_im_rendering` / `test_wake_continuity_injection` / `test_session_init_message_ids` 全部通过，无回归
- [ ] 集成端到端（staging）：
  - [ ] 连续对话 5 轮 → agent 回复 "好" → `subagent_rest(rest_duration_minutes=1)`
  - [ ] 等 70s 唤醒
  - [ ] 首轮 think 的 LLM input 含 WAKE_IM_REPLAY 段（5 轮历史）
  - [ ] 第二轮 think 不再重复注入（flag 已清）

## 可观测性 Checklist

- [x] metric `wake_im_replay_total{result=injected|skipped_empty}` counter
- [x] metric `wake_im_replay_messages` histogram（每次回放了多少条）
- [x] metric `wake_im_replay_tokens` histogram
- [x] log (context.read 首次): `[wake_im_replay] scope=... agent=... messages=N tokens~T`
- [x] log 软失败路径全部 `logger.warning` + 降级，不静默吞
- （说明）`skipped_disabled` 没出现是因为 kill switch 在函数入口早返回，不再走到计数点——通过 log 里"没有 `[wake_im_replay]` 行"就能辨识；等后续有需要再补。

## 文档 Checklist

- [x] [message-wake-refactor.md](../message-wake-refactor.md) R9 小节追加 P6-3 进度
- [x] 本工单 Status → `[x]`
- [ ] 运营 runbook：如何关闭（`WAKE_IM_REPLAY_ENABLED=0`）——与 PR-41/42 staging verification runbook 合并
- [ ] [docs/cortex/context-timeline-and-dfs.md](../../cortex/context-timeline-and-dfs.md) 描述"wake 首轮"注入顺序（可与 PR-43 一起落）

## 验收命令

```bash
# 1) 制造对话 + rest
# 连续聊 5 句 → subagent_rest(1 min)

# 2) 唤醒后取 scope 的 round1 context
sleep 70
curl -s .../cortex/v1/scope/$NEW/context?round=1 \
  | jq '.messages[] | select(._message_type=="WAKE_IM_REPLAY")' | length
# → 期望：5

# 3) round 2 不应再有
curl -s .../cortex/v1/scope/$NEW/context?round=2 \
  | jq '[.messages[] | select(._message_type=="WAKE_IM_REPLAY")] | length'
# → 0
```

## 部署 Checklist（必走，不部署不算完成）

- [ ] **本地代码已合入 main**：`git log --oneline origin/main | rg PR-44`
- [ ] **runtime 子模块已 bump** 并推到父仓库远端
- [ ] **已 deploy**：父仓库根 `./deploy runtime`
- [ ] **线上证据 1 — flag 落盘**：任一新 wake 后 `ssh api.gradievo.com 'grep -E "wake_im_replay" /opt/novaic/logs/runtime*.log | tail -10'` 有 `[wake_im_replay] scope=... messages=N tokens~T` 行
- [ ] **线上证据 2 — 指标**：`curl -s https://api.gradievo.com/metrics | rg 'wake_im_replay_total'` injected 计数器 > 0
- [ ] **线上证据 3 — 幂等**：再次 context.read 同一 scope（round 2）时，日志不再出现新 wake_im_replay 行；`_message_type=WAKE_IM_REPLAY` 不该永久写进 context.jsonl（ephemeral）
- [ ] 把上述三段 paste 进 PR 关单评论
- [ ] 如需临时禁用：`WAKE_IM_REPLAY_ENABLED=0` 写入 runtime 的 env，重启 runtime 即可（不需要回滚代码）

## 回滚

- 单 env `WAKE_IM_REPLAY_ENABLED=0` 即可停用
- 已注入过的历史 scope 不受影响（过去的 context.jsonl 已写入，回滚不会删）
- 彻底回滚：revert commit

## 风险 / 讨论

1. **与 PR-43 的重叠**：如果 PR-43 的 PREV_SCOPE_TAIL 已包含上一次 scope 里的 AGENT_REPLY step，本 PR 又从 chat_messages 拉 AGENT_REPLY → 重复。mitigation：回放默认排除"已在 PREV_SCOPE_TAIL 中出现的 AGENT_REPLY"（通过 message_id 比对）。可简化为"本 PR 默认开启但建议在 PR-43 上线后重新评估 K 值"。
2. **K 值选择**：K=20 是保守默认；真实情况下 LLM context 4k-8k token 预算可能只容 5-10 条。
3. **噪音**：某些 agent 历史 IM 流是纯交付，回放可能帮助有限。**可按 subagent 级别开关**（配置 `subagents.wake_im_replay_enabled`）—— 本 PR 不做，留给运营观察。
4. **顺序敏感**：WAKE_IM_REPLAY 放在 PREV_SCOPE_TAIL 之后 vs 之前？推荐**之后**，因为 tail 是"工具轨迹"，chat 是"用户对话"，LLM 先看工具再看对话更符合认知顺序。

## 备注

- 本 PR 与 PR-43 正交 —— 一个 agent 可能完全不用工具（纯对话场景），PREV_SCOPE_TAIL 近乎空，此时 IM REPLAY 承担全部续接职责；反之亦然。
- 长期方向：把 PR-42/43/44 三个注入点统一抽象成 `WakeContinuityAssembler`，按 trigger_type 决定注入哪几层、每层分多少预算。本 PR 不做该抽象，等三层都稳定后再重构。

