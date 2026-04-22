# PR-48  Turn Finalizer：LLM 一轮对话后强制收敛 scope（rest / skill_end 自动补齐）

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix + convention hardening |
| **Milestone** | R8（状态机化的最后一公里） |
| **承诺** | R8 + R9（scope 能关才能"醒来拿上下文"） |
| **Status** | `[✓]` — **已部署 prod 2026-04-22 18:00 UTC**。`WAKE_TURN_FINALIZER_ENABLED=True`、`closer_tools=['chat_reply']` 在线验证加载成功；下一轮真实连聊后观察 `turn_finalizer_total{reason="reply_no_followup"}` 指标 |
| **Depends on** | PR-28（subagent 状态机）、PR-29（scope 状态机）、PR-45（text 层，依赖 rest 产出 historical_summary） |
| **Blocks** | PR-42/44/45 真正生效；PR-43（scope chain 必须 scope 能被关才能有"上一次") |
| **估时** | 1 d |
| **Owner** | __ |
| **PR 标题** | `fix(runtime): auto-finalize agent turn when LLM replies without calling rest/skill_end` |

## 事件摘要

04-22 观察到的一连串问题里，**根因 D** 是所有连锁反应的起点：

> Agent 在 chat_reply 之后不 subagent_rest 也不 skill_end。scope 永远 `running`，新消息全部走 "buffered" 分支（`handle_buffered_message_enqueue`，直接 `append_scope_input` + 唤醒正在跑的循环）。

直接后果：

1. **PR-42/44/45 注入路径全部空跑**。`handle_session_init` 只在**新 scope 开启**时才把 `<HANDOFF_NOTES> / <HISTORICAL_SUMMARY> / <CHAT_HISTORY>` 插 `initial_context`。scope 一直不死 → session.init 从不再跑 → continuity 段永远不会出现。用户看到"dfs scope 没加载"其实就是"scope 根本没重新开"。
2. **subagents.historical_summary 字段永远是 NULL**。只有 `subagent_rest` saga 走完 `generate_simple_summary → handle_subagent_set_sleeping` 才能写入。agent 不 rest → 字段永远空 → 就算 PR-42/45 的 continuity 注入代码跑到了也是空字符串。
3. **HealthWorker orphan 误判概率放大**。scope 一直 running，outbox 消费速度 ≠ runtime 消化速度；`message_outbox.attempts` 累计到 3 就 PERMANENT_ORPHAN，本来能正常消化的消息被提前打成死信。
4. **Cortex scope 内存无界增长**。单个 scope 的 context.jsonl 无限 append（11 条 user + 11 轮 thinking + 11 个 chat_reply + 无数 no-tool 提醒…）。上下文窗口打满之前，LLM 质量已经断崖。

### 为什么 agent 不主动 rest

翻 tool_handlers.py 和 LLM 系统 prompt：

- `chat_reply` 工具的 tool_handlers 里**没有任何终止 scope 的副作用**。它只是把 reply 写进 `chat_messages`，发给用户的 IM。
- `subagent_rest` 工具**根本没有对应的 executor**（PR-49 会补，此处是 blocker 事实）；LLM 即使想 rest，工具调用也会落进 "未知工具" 分支被拒。
- `skill_end` 有 executor，但它关的是 skill 栈顶 scope，不是 subagent 主 scope；agent 并不知道应该在 `chat_reply` 后 `skill_end(scope_id=main_scope)`。
- 系统 prompt 里对"chat_reply 之后要做什么"语焉不详，LLM 就在 no-tool warning 的狼嚎里反复 chat_reply + 自言自语。

**结论**：不能指望 LLM 自己礼貌关门。必须 runtime 侧硬托底。

## 方案

**双保险**：

1. **硬约束（Runtime 强制）**：chat_reply 之后若 LLM 下一轮不调任何工具且无新用户消息，runtime 直接触发 `subagent_rest` saga，关 scope。
2. **软约束（Prompt/Convention 对齐）**：LLM 正确路径是 `chat_reply → subagent_rest(handoff_notes=...)`；prompt 明确化，配合 PR-49 的 executor 让 LLM 能真的调用。

本 PR 专注硬约束（软约束由 PR-49 + prompt PR 解决）。

### A. Turn Finalizer：saga_worker 层的收敛决策

在 `novaic-agent-runtime/task_queue/workers/saga_worker_sync.py`（think-loop 主驱动）新增 `_should_finalize_turn` 钩子：

```python
# saga_worker_sync.py（想法示意，不是最终形态）
def _should_finalize_turn(self, llm_output, scope_ctx) -> FinalizeReason | None:
    """
    判定"一轮 dispatch 该不该结束"。返回 None = 继续；返回 reason = 立即 finalize。
    """
    # 1. LLM 说完 chat_reply 又没调其他工具
    if (llm_output.last_tool == "chat_reply"
            and not llm_output.other_tool_calls
            and scope_ctx.no_pending_user_messages):
        return FinalizeReason.REPLY_NO_FOLLOWUP

    # 2. LLM 连续 N 轮 no-tool（PR-37 已显式信号）
    if scope_ctx.no_tool_warnings_consecutive >= MAX_NO_TOOL_BEFORE_FINALIZE:
        return FinalizeReason.NO_TOOL_LOOP

    # 3. 单轮 dispatch think 步数超过上限
    if scope_ctx.think_rounds >= MAX_THINK_ROUNDS_PER_DISPATCH:
        return FinalizeReason.THINK_CAP

    return None

def _finalize_turn(self, reason: FinalizeReason, scope_ctx):
    """显式触发 subagent_rest saga。日志标注 reason，方便事后统计。"""
    logger.info(
        "[turn_finalizer] forcing rest scope=%s reason=%s",
        scope_ctx.scope_id, reason.value,
    )
    metric_inc("turn_finalizer_total", reason=reason.value)
    # 直接触发 subagent_rest saga（不依赖 LLM tool call）
    self.queue_client.create_saga(
        "subagent_rest",
        agent_id=scope_ctx.agent_id,
        subagent_id=scope_ctx.subagent_id,
        # 没有 LLM 提供的 handoff_notes；historical_summary 由 saga
        # 内部 generate_simple_summary 步骤兜底
        handoff_notes=None,
        wake_reason="auto_finalize",
    )
```

**三个触发条件**：

1. **REPLY_NO_FOLLOWUP**：LLM 说完话没下文——正常对话结束，该休息。
2. **NO_TOOL_LOOP**：LLM 连续 no-tool 3 轮（PR-37 的 warning 已显式计数）——LLM 搞不清方向，强制终止防内存爆。
3. **THINK_CAP**：单轮 dispatch think 步数超 20——兜底防止死循环。

### B. subagent_rest saga 可被 runtime 主动 enqueue（不依赖 LLM）

当前 `subagent_rest` saga 只由 LLM tool 调用驱动。PR-49 会补 executor，但本 PR 需要**runtime 直接 enqueue saga**——绕过 LLM 工具层。

- Queue Service 已支持 `create_saga` API（被 gateway、business 都用）。
- 加一条 "actor" 区分：`actor="runtime.turn_finalizer"` vs `actor="llm.tool.subagent_rest"`，`subagent_state_transitions` 表（PR-31）里能分开统计。
- `handoff_notes=None` 的 rest 是合法的；saga 内部 `generate_simple_summary` 步骤兜底产 summary。

### C. scope 内存 / think 步数上限

- `MAX_THINK_ROUNDS_PER_DISPATCH`（env，默认 20）：单次 dispatch 内 LLM think → act 循环次数。
- `MAX_NO_TOOL_BEFORE_FINALIZE`（env，默认 3）：连续 no-tool warning 计数阈值，触发 finalize。
- 两个值都配置化，出事 ops 能快速收紧/放宽。

### D. 观测信号

- `metric_inc("turn_finalizer_total", reason=...)`
- 日志 `event=turn_finalizer scope=X reason=Y think_rounds=N`
- 新增 Grafana 看板行：`rate(turn_finalizer_total[5m]) by (reason)`

理想稳态：`REPLY_NO_FOLLOWUP` 占 95%+；`NO_TOOL_LOOP` / `THINK_CAP` 近 0；非 0 = 有异常 agent / prompt bug。

## 范围

### runtime
- `novaic-agent-runtime/task_queue/workers/saga_worker_sync.py`：加 `_should_finalize_turn` + `_finalize_turn`
- `novaic-agent-runtime/task_queue/workers/saga_worker_sync.py`：think-loop 每轮调用 `_should_finalize_turn`
- 新增 env: `MAX_THINK_ROUNDS_PER_DISPATCH`、`MAX_NO_TOOL_BEFORE_FINALIZE`
- `novaic-agent-runtime/tests/test_turn_finalizer.py`

### business/queue
- `subagent_rest` saga 支持 `actor` 字段（可选）；已存在则零改动
- 验证 `create_saga("subagent_rest", ...)` 从 runtime 直接调合法（不缺前置步骤）

### prompt（下游 PR）
- 本 PR **不改 prompt**；系统 prompt 的终止约定由 PR-49（executor）+ 另一个 prompt PR 对齐。
- 本 PR 只做 runtime 硬托底——这是"即使 LLM 乱写 prompt，系统也能收敛"的底线。

## 实施 Checklist

### A. runtime turn finalizer（Wave 1 — 已实现）
- [x] 实现位置由 `saga_worker_sync` 调整为 `react_actions._decide_rest_or_continue` — 那里原本就是"是否该 rest"的决策节点，已有 `force_rest_reason` 字段，最小入侵
- [x] REPLY_NO_FOLLOWUP 路径：`_is_reply_no_followup(ctx["tool_calls"])` 命中 → `force_rest_reason="reply_no_followup"`，`stack_empty=True`（无视 Cortex stack depth）
- [x] 优先级 REPLY_NO_FOLLOWUP > round_cap > stack_unknown(→think) > stack_empty(→rest) > stack_nonempty(→think)
- [x] Kill switch `WAKE_TURN_FINALIZER_ENABLED`（默认 1）
- [x] Turn-closer 工具集 env 化 `WAKE_TURN_CLOSER_TOOLS`（默认 `chat_reply`）
- [x] 日志 `event=turn_finalizer scope=X reason=reply_no_followup stack_depth=N tool_calls=[...]`
- [x] Metric `turn_finalizer_total{reason}`（复用 `common.utils.metrics.metric_inc`）
- [x] `_build_trigger_rest_payload` 原本就透传 `force_rest_reason` → saga context `rest_reason="reply_no_followup"`

### A-延后（Wave 2 — 如线上指标异常再追加）
- [ ] NO_TOOL_LOOP 独立 finalizer（当前已被 round_cap 覆盖，够用）
- [ ] saga_worker_sync 层全局 think-loop 硬 cap（双保险）
- [ ] env `MAX_THINK_ROUNDS_PER_DISPATCH` / `MAX_NO_TOOL_BEFORE_FINALIZE`（Wave 2 再引入）

### B. saga 兼容
- [x] `subagent_rest` saga 透传新 reason（仅字符串，无需改 saga 定义）
- [x] idempotency key 仍 `subagent-rest-{scope}-r{round}` — 无重复 saga 风险

### C. 单测（`tests/test_pr48_turn_finalizer.py`，16 个）
- [x] `_is_reply_no_followup` 纯函数覆盖：单 chat_reply / 多 chat_reply / 混合非 closer / 无 chat_reply / 空列表（heartbeat）/ 畸形 tool_call / `WAKE_TURN_CLOSER_TOOLS` env override
- [x] REPLY_NO_FOLLOWUP + stack_depth=1 强制 rest（headline bug 守护）
- [x] REPLY_NO_FOLLOWUP + stack_known=False 也强制 rest（fail-safe）
- [x] 非 closer 工具 + 非空 stack 仍 think（回归守护）
- [x] chat_reply + plan_update 同轮 → 不 finalize（中间消息语义）
- [x] 空 stack 无 closer → 自然 rest（force_rest_reason=None）
- [x] round_cap 在 REPLY_NO_FOLLOWUP 缺席时仍触发
- [x] Kill switch `WAKE_TURN_FINALIZER_ENABLED=0` 完全回滚 pre-PR-48 行为
- [x] `_build_trigger_rest_payload` 携带 `rest_reason="reply_no_followup"` + `stack_depth_at_rest=1`
- [x] 自然 rest 仍 `rest_reason="stack_empty"`（reason 枚举不退化）

### D. 回归
- [x] 全 `novaic-agent-runtime` 套件 192 个全绿（含 PR-41 / PR-45 / PR-46 / PR-49 历史单测）

## 验收

### 本地
```bash
cd novaic-agent-runtime && ./run_tests.sh tests/test_turn_finalizer.py tests/test_saga_worker_sync.py tests/test_pr45_continuity_wiring.py
```

### 线上
```bash
# 1. 发一条 user_message → LLM chat_reply → ...
# 2. 观察 runtime 日志
grep 'event=turn_finalizer' /opt/novaic/data/logs/runtime-*.log | tail -5
# 预期：REPLY_NO_FOLLOWUP 命中，且同一 agent 的 scope 在 <30s 内走完 subagent_rest saga
#
# 3. 验证 subagents 表 historical_summary 被写入
ssh prod sqlite3 /opt/novaic/data/entangled.db \
  "SELECT subagent_id, historical_summary, status FROM subagents WHERE agent_id='<aid>' ORDER BY updated_at DESC LIMIT 3;"
# 预期：status='sleeping'，historical_summary 非空
#
# 4. 再发一条 user_message，观察新 scope 的 session.init 命中 continuity 注入
grep 'event=continuity_injected' /opt/novaic/data/logs/runtime-*.log | tail -3
# 预期：handoff_notes 空 / historical_summary 非空（因为上一轮 summary 已经写入）
```

## 部署 Checklist（必走）

1. 代码合入父仓 main
2. `./deploy runtime`
3. 线上证据 ≥ 3 段：
   - `turn_finalizer_total{reason="REPLY_NO_FOLLOWUP"}` ≥ 1（近 1h）
   - 同 agent 的 subagents 行 status='sleeping' 且 historical_summary 非空
   - 紧随其后的 user_message 触发的新 scope，session.init 日志命中 continuity 注入（PR-45 已经有 metric `wake_continuity_injected_total`）
4. 负向：`turn_finalizer_total{reason="NO_TOOL_LOOP"}` + `{reason="THINK_CAP"}` 近 1h < 5 次（偶发允许；持续高频说明 prompt 或 tool 有问题，需进一步排查）

## 风险 / 讨论

1. **"强制 rest" 会不会把正在思考的 agent 打断**：
   - `REPLY_NO_FOLLOWUP` 仅在 LLM 明确说完话（chat_reply）后才触发——这是语义正确的"说完了就休息"。
   - `NO_TOOL_LOOP` / `THINK_CAP` 触发时 agent 实际上已经陷在异常循环，打断是对的。
2. **LLM 主动 `subagent_rest` 和 finalizer 双触发 race**：顺序上 LLM 工具调先（think-loop 当轮处理），finalizer 判定在这轮结束之后。LLM 成功调 rest → 当前 scope 已进入 sleeping 状态机，finalizer 条件 1（`last_tool == chat_reply`）不成立，自然不重复触发。
3. **IM 消息"来得巧"**：finalizer 决定要 rest 的一瞬间来了新 user message——走 buffered 路径追加到 scope.input_message_ids，finalizer enqueue 的 rest saga 开始执行时可以 cancel，或者 rest 完成后新消息重新触发 dispatch（PR-46 by-ids 装配保证新 scope 只吃新消息）。**选择后者**（cancel 太复杂）：rest 完成后，新消息由 subscriber 正常下发，开新 scope，走完整 session.init 路径——正好是 PR-42/44/45 想要的理想形态。
4. **chat_reply cap 和 finalizer 冲突**：PR-45 的 `chat_reply cap=N` 已经对单 scope 内的 reply 次数设上限。两个机制不冲突：cap 先触发 → LLM 看到 rate-limit 错误；finalizer 再兜底触发 rest。
5. **THINK_CAP 值**：20 对正常对话足够；复杂工具链（shell + grep + edit 组合）可能接近这个数。如果发现正常 agent 被误杀，调大到 40。
6. **是否需要 "等 LLM 主动 rest 30s 再 finalize"**：不需要。LLM 的 think 是同步的——当轮不 rest 就永远不 rest。等反而增加 scope 滞留时间。

## 承诺登记

- **R8**：scope 状态机有了终点。之前的 PR 建好了状态枚举和 transition 日志，但"凭什么进入终态"一直靠 LLM 自觉；本 PR 让 runtime 对这条约束硬托底。
- **R9**：只有 scope 能关，才有"上一次 scope 的尾部"可以在下一次醒来时读。这是 R9 从纸面承诺到代码生效的最后一块。

## 备注

- 本 PR **一定要和 PR-49 一起或紧随其后上**：本 PR 托底 LLM 不 rest，PR-49 让 LLM 能自己 rest。两者一起才是"正常路径 + 兜底"的完整闭环。
- prompt 调整（强化 "chat_reply → subagent_rest" 惯例）可单独开 PR，不 blocker。
