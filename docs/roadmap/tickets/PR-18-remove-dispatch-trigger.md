# PR-18  删除 Business `_dispatch_trigger`

| 字段 | 值 |
| --- | --- |
| **Phase** | 2 |
| **Milestone** | M2 |
| **承诺** | R1 + R6 |
| **Status** | `[x]` (merged; see roadmap README index) |
| **Depends on** | PR-17（观察期通过） |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | __ |
| **PR 标题** | `refactor(business): remove _dispatch_trigger; subscriber is now sole dispatcher` |

## 目标

彻底摘掉写入处的 dispatch 责任。subagent_send / spawn_subagent 的 handler 只写 Entangled；outbox + subscriber 负责后续。

## 范围

- `novaic-business/business/internal/subagent.py`
- 所有调 `_dispatch_trigger` 的处（grep 确认）

## 前置 Checklist

- [ ] PR-17 合并 + 稳定运行 ≥ 24-48h
- [ ] outbox lag / subscriber 失败率均达标
- [ ] `subagent_send` / `spawn_subagent` 的消息**确定**会在 PR-14 的路径里被写 outbox（**关键核对点**）

## 实施 Checklist

### 确认 outbox 覆盖

- [ ] `subagent_send` 最终写 `chat_messages`？若否 → 本 PR 阻塞，需要先扩展 outbox 覆盖其它实体
- [ ] `spawn_subagent` 最终写 `chat_messages`？若否 → 同上
- [ ] 本地复现：发 SUBAGENT_SEND → 看 outbox 表 → 确认有对应行

### 删除

- [ ] 删 `_dispatch_trigger` 函数定义
- [ ] 删所有调用方（`subagent_send` / `spawn_subagent` handler 中的 fire-and-forget 调用）
- [ ] 删相关的 import / helper

### 验证路径不减

- [ ] subagent_send API 端到端：发 → 子 agent 被唤醒（现在路径：API → 写 chat_messages + outbox → subscriber → Queue → scope）
- [ ] spawn_subagent API 同上

### CI 清理

- [ ] PR-03 allowlist 中 `subagent.py` 条目删除
- [ ] `rg '_dispatch_trigger' novaic-business/` 应当为空

## 测试 Checklist

- [ ] 单测：subagent_send 端点 → 写 chat_messages，不再有任何 HTTP post 到 `/dispatch`
- [ ] 集成：
  - 发 SUBAGENT_SEND → outbox 有行 → subscriber 消费 → Queue 收到 → 子 agent 唤醒
  - 压测：并发 SUBAGENT_SEND 100 条 → 无漏

## 可观测性 Checklist

- [ ] metric `dispatch_total{caller=business}` 应 → 接近 0（因为 Business 不再主动 dispatch）
- [ ] metric `dispatch_total{caller=business-subscriber}` 是新的主要贡献者

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P2-4 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] `HANDOVER.md` 追加一条"最后更新"

## 验收命令

```bash
rg '_dispatch_trigger' novaic-business/
# 预期：空

# 端到端：发 SUBAGENT_SEND，观察链路
# 1. chat_messages 有行
# 2. outbox 有行
# 3. subscriber 消费日志
# 4. Queue Service /dispatch 收到 1 次
# 5. 子 agent 唤醒
```

## 回滚

- revert 本 PR
- 若 subscriber 出现灾难性 bug 而不想回滚 PR-17 的 flag：
  1. revert 本 PR（恢复 `_dispatch_trigger` 薄壳） 
  2. subscriber 仍开着但与 `_dispatch_trigger` 并存 → Queue Service idempotency ledger 兜住重复

## 备注

- **不**在本 PR 里删 `_dispatch_trigger` 的薄壳同时删 subscriber；那样会有窗口期无人 dispatch。
- 做这步之前，请再看一次 PR-17 观察期的 "红线"—— 如果有未解决的告警，不要做这一步。
