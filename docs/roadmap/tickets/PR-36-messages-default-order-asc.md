# PR-36  修复用户消息到 LLM context 的顺序（messages 默认排序 ASC + 拉取显式 ASC）

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（Cortex context assembly 四连击 #1/4 — 最高优先级、代码改动最小） |
| **Milestone** | — |
| **承诺** | 架构原则：**无静默失败** + **系统简单** |
| **Status** | `[x]` 2026-04-22 完成 — caller-side 显式 ASC + schema 默认 ASC + 3 unit tests |
| **Depends on** | — |
| **Blocks** | PR-38（IM 渲染在正序之上才有意义） |
| **估时** | 0.25 d |
| **Owner** | wangchaoqun |

## 事件摘要

用户连发 `A → B → C` 三条消息，Agent 看到的却是 `C → B → A` —— 理解完全反。

**根因**（代码层铁证）：

1. `novaic-business/business/schema_push.py:411`：
   ```python
   MESSAGES_DEF = SqlEntityDef(
       name="messages",
       table="chat_messages",
       ...
       default_order="timestamp DESC",
       ...
   )
   ```
2. `novaic-agent-runtime/task_queue/handlers/context_handlers.py:54`：
   ```python
   all_messages = business_client.entity_list(
       "messages",
       params={"agent_id": agent_id, "read": "0"},  # 没传 order_by
   )
   ```

结果：Business 按 `timestamp DESC` 返回未读消息 → runtime 按此顺序 `bridge.append_context(...)` 追加进 `context.jsonl` → 最新一条反而写在最前，倒序送入 LLM。

## 修复方案（两层）

### A. Caller 侧显式 `order_by="timestamp ASC"`（**belt，立即生效**）

`context_handlers.handle_context_read` 在 `entity_list("messages", ...)` 调用时显式传 `order_by`：

```python
all_messages = business_client.entity_list(
    "messages",
    params={
        "agent_id": agent_id,
        "read": "0",
        "order_by": "timestamp ASC",
    },
)
```

`novaic-business/business/internal/entity.py:_split_scope` 已经支持从 params 里抽 `order_by`（line 44），零侵入。

### B. Schema 默认改 `timestamp ASC`（**suspenders，根因**）

`MESSAGES_DEF.default_order` 改为 `"timestamp ASC"`。理由：

- `chat_messages` 表的业务语义是 **IM 流水**，append-only，消费端天然 ASC。
- 目前依赖 DESC 默认的地方：UI 列表（最新在前）——这些 caller **已经在自己代码里显式传 `order_by="timestamp DESC"` 或 `limit` + 隐式 DESC**？需审计。如果找到依赖隐式 DESC 的 caller，给它们显式 DESC，再改默认。
- **审计清单**（grep 基线）：
  ```bash
  rg -n 'entity_list\("messages"|entity_list\(\s*"messages"' --type py
  rg -n 'entity_list\(\s*"chat_messages"|entity_list\("chat_messages"' --type py
  ```
  本 PR 只审计 backend；frontend 的 reactive subscription 订阅走 Entangled 直连，默认 order 行为需单独走 PR-40+ 对齐。

### C. 回归测试

`novaic-agent-runtime/tests/test_context_read_ordering.py` 新增：

- **happy path**：3 条未读 `timestamp=t1,t2,t3 (t1<t2<t3)`，`handle_context_read` 追加 context 顺序为 `t1, t2, t3`。
- **regression guard**：mock Business `entity_list` 接受 `order_by="timestamp ASC"` → 断言参数内含 `order_by=timestamp ASC`（防止 caller 回退到默认）。

## 子 PR

| # | Repo | Branch | 内容 |
|---|---|---|---|
| 1 | `novaic-agent-runtime` | `hotfix/context-read-order-asc` | A：`context_handlers.py` 传 `order_by=timestamp ASC` + 新增 2 unit tests |
| 2 | `novaic-business` | `hotfix/messages-default-order-asc` | B：`MESSAGES_DEF.default_order="timestamp ASC"` + 现有调用方审计 |
| — | 主仓 | `fix/cortex-context-assembly-36-39` | submodule bumps + HANDOVER |

**Merge 顺序**：1 先单独可 merge（belt 生效）。2 依赖 1 落地稳定 + 调用方审计通过。

## 验收

- 新 test 通过。
- 手动验证：向 prod agent 连发 3 条消息，`/v1/internal/messages/{id}/trace` 的 scope 内 assistant 回复能正确引用 3 条消息的**实际时间顺序**（从 "A" 开始回复，不是从 "C"）。
- `HANDOVER.md` 追一条 "2026-04-22：修正用户消息倒序 bug（PR-36）"。

## 回滚

`git revert <commit>` — 恢复原状（DESC）。无 schema migration 风险（default_order 是 read-side 配置，不改存储）。

## 架构判定沉淀

- **默认参数的方向性要匹配业务语义**：append-only 流水表默认 ASC；状态更新表（`created_at DESC`）默认 DESC。未来所有 `SqlEntityDef` 声明 `default_order` 时 code review 检查点：是否与该 entity 的主消费模式对齐。
