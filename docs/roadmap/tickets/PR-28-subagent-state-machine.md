# PR-28  Subagent 状态机（`subagent_state.transition` 唯一入口）

| 字段 | 值 |
| --- | --- |
| **Phase** | 5（状态机化，长期） |
| **Milestone** | M4 |
| **承诺** | R8 |
| **Status** | `[x]` (2026-04-15) |
| **Depends on** | M2 达成 |
| **Blocks** | PR-31 |
| **估时** | 1.5 d |
| **Owner** | 2026-04-15 |
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

---

## 实施总结（2026-04-15）

### 代码
- **新增 `novaic-business/business/internal/subagent_state.py`**：
  - `SubagentStatus` 枚举再导出（权威：`common.enums`）。
  - `ALLOWED` 转移矩阵 —— 终态 `completed` / `cancelled` 出度为空；`failed`
    仅能恢复到 `sleeping` / `awake`。
  - `transition(store, subagent_id, agent_id, *, to, reason, actor, extra=None)`：
    - 读取当前状态 → 校验 `ALLOWED` → 原子写 `status + extra`；
    - 自环（current == to）短路返回 `{"noop": True}`，不升计数器；
    - 合法写后发日志行 `subagent_state subagent=<sid> <from> -> <to> reason=... actor=...`
      并在模块级 `_transitions` Counter 累加（PR-31 会迁到持久表）。
  - 便捷 wrapper：`mark_sleeping` / `mark_awake` / `mark_completed` /
    `mark_failed` / `mark_cancelled`。
  - 例外：`InvalidTransition`、`SubagentNotFound`。
- **`business/internal/entity.py` 的通用 PATCH**：当 `entity == "subagents"`
  且 payload 带 `status` 时，强制改走 `subagent_state.transition(...)`。
  允许 payload 额外字段 `_transition_reason` / `_transition_actor` 提示
  来源；否则默认 `entity_update` + `X-Internal-Service` caller。非法转移
  返回 409。
- **业务侧 7 个散落 `UPDATE subagents SET status` 点全部迁移**：
  - `internal/subagent.py` PATCH / timeout / cancel；
  - `internal/agent.py` timeout / cancel；
  - `internal/message.py` 的 interrupt；
  - `agent_actions.py` 的 interrupt；
- **Runtime 3 个 `entity_update("subagents", ...)` 点**（`subagent_handlers.py`）
  在 payload 里显式挂 `_transition_reason` + `_transition_actor`，由
  Business 端 entity.py 统一下放到 `transition()`。

### 测试
- `novaic-business/tests/test_subagent_state.py` 22 个用例覆盖：
  - 合法 / 非法转移矩阵（含终态）；
  - 自环 noop 不升计数器，但 `extra` 仍会写入；
  - `SubagentNotFound`；
  - `extra` 禁止含 `status` key；
  - 所有 `mark_*` wrapper 的 payload 形状；
  - metric key 格式 `<from>-><to>/<reason>`；
  - Entity PATCH 端点：强制走 transition、非法返回 409、缺 `agent_id` 返 400。

### CI Lint
- `scripts/ci/lint_subagent_status.sh`：`rg` 扫 `store.update` /
  `entity_update` / `.update(... "subagents" ... "status")` 三种 pattern，
  allowlist = `subagent_state.py` + `entity.py` + `subagent_handlers.py`
  + `schema_push.py` + `tests/` + `docs/`。任何新增写入点都会红。
- 已挂入 `.github/workflows/lint.yml`。

### 验收
- `bash scripts/ci/lint_subagent_status.sh` → `subagent_status lint OK`。
- `cd novaic-business && pytest --ignore=tests/test_schema_invariants.py`
  → 75 passed。
- 生产 smoke：新造一次 subagent wake 循环，查 `rg "subagent_state subagent="
  /var/log/novaic/*.log` 可按 `<from> -> <to> reason=... actor=...` 追踪。
