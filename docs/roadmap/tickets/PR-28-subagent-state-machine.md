# PR-28  Subagent 状态机（`subagent_state.transition` 唯一入口）

| 字段 | 值 |
| --- | --- |
| **Phase** | 5（状态机化，长期） |
| **Milestone** | M4 |
| **承诺** | R8 |
| **Status** | `[ ]` |
| **Depends on** | M2 达成 |
| **Blocks** | PR-31 |
| **估时** | 1.5 d |
| **Owner** | __ |
| **PR 标题** | `refactor(business): subagent status via single state_transition entry` |

## 目标

废除 "多字段拼状态" 反模式（`status / wake_at / need_rest / summary_lock`）的散落 `UPDATE`，所有状态变更走唯一入口 `subagent_state.transition(...)`。

## 范围

- `novaic-business/business/internal/subagent_utils.py`（新增 state 模块或扩展现有）
- 所有当前直接 `UPDATE subagents SET status=...` 的位置

## 前置 Checklist

- [ ] `rg "UPDATE subagents.*SET.*status" novaic-*/` 清点待迁移点
- [ ] Subagent 当前 status 枚举有哪些值 → 先把权威列表写死

## 实施 Checklist

### 1. 权威枚举 + 转移表

```python
# business/internal/subagent_state.py
class SubagentStatus(str, Enum):
    ACTIVE        = "active"
    SLEEPING      = "sleeping"
    ARCHIVED      = "archived"
    FAILED        = "failed"
    # 根据当前实际值扩充

ALLOWED = {
    SubagentStatus.ACTIVE:   {SubagentStatus.SLEEPING, SubagentStatus.ARCHIVED, SubagentStatus.FAILED},
    SubagentStatus.SLEEPING: {SubagentStatus.ACTIVE,   SubagentStatus.ARCHIVED, SubagentStatus.FAILED},
    SubagentStatus.ARCHIVED: set(),    # terminal
    SubagentStatus.FAILED:   {SubagentStatus.ACTIVE, SubagentStatus.ARCHIVED},
}

def transition(store, subagent_id, *, to: SubagentStatus, reason: str, actor: str):
    # read current
    cur = store.get("subagents", subagent_id)["status"]
    if SubagentStatus(to) not in ALLOWED[SubagentStatus(cur)]:
        raise InvalidTransition(f"{cur} -> {to}")
    store.update("subagents", subagent_id, {"status": to.value})
    _log_transition(store, subagent_id, cur, to.value, reason, actor)
```

### 2. 迁移调用点

- [ ] `spawn_subagent` → `transition(..., to=ACTIVE, reason="spawn", actor=...)`
- [ ] `subagent_rest` → `transition(..., to=SLEEPING, reason="rest", ...)`
- [ ] scheduler 唤醒 → `transition(..., to=ACTIVE, reason="scheduled_wake", ...)`
- [ ] archive → `transition(..., to=ARCHIVED, ...)`
- [ ] 失败分支 → `transition(..., to=FAILED, reason=..., ...)`

### 3. 其余字段语义

- [ ] `wake_at`、`wake_triggers`、`need_rest`、`summary_lock` 收进 metadata：仅辅助字段，**不**参与状态判定
- [ ] 与 status 正交；例如 `status=ACTIVE AND wake_at=null` 是合法的（正在工作）

### 4. CI lint

- [ ] 类似 PR-03：禁止业务代码直接 `UPDATE subagents SET status`（allowlist: `subagent_state.py`, `tests/`, `migrations/`）

## 测试 Checklist

- [ ] 单测：所有合法转移
- [ ] 单测：非法转移 raise `InvalidTransition`
- [ ] 迁移后：所有调用点用 `transition`；无 `UPDATE ... status` 散落

## 可观测性 Checklist

- [ ] metric `subagent_transitions_total{from, to, reason}` counter
- [ ] log：`subagent_state subagent=... <from> -> <to> reason=...`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P5-1 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] [architecture/entity-data-models.md](../../architecture/entity-data-models.md) 更新 Subagent 字段表

## 验收命令

```bash
rg 'UPDATE subagents.*SET.*status' novaic-*/ | rg -v 'subagent_state.py|tests/|migrations/'
# 预期空
```

## 回滚

`git revert` —— 旧 `UPDATE` 路径回来。

## 备注

- 这是长期重构的开始；同类做法会延伸到 Scope / Message (PR-30) / Saga / Task。
- PR-31 会把 transitions 写入持久 log 表（此 PR 先进 metric/log 级别）。
