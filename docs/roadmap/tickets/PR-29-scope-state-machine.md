# PR-29  Scope 状态机（Cortex 内部）

| 字段 | 值 |
| --- | --- |
| **Phase** | 5 |
| **Milestone** | M4 |
| **承诺** | R8（与 INV-5/6 协同） |
| **Status** | `[x]` (2026-04-15) |
| **Depends on** | M2 达成 |
| **Blocks** | PR-31 |
| **估时** | 1.5 d |
| **Owner** | 2026-04-15 |
| **PR 标题** | `refactor(cortex): scope state enum + scope_state.transition()` |

## 目标

Cortex 内部的 scope 生命周期目前由多个 "存在性 + meta.json 字段" 组合隐式表达。引入明确 `ScopeState` 枚举和转移表，配合 INV-5/6（幂等 end / archive 方向）。

## 范围

- `novaic-cortex/novaic_cortex/scope.py`（或等价）
- `novaic-cortex/novaic_cortex/api.py`（转移调用点）
- scope `meta.json` 增加 `state` 字段

## 前置 Checklist

- [ ] 与 [cortex/invariants.md](../../cortex/invariants.md) 的 INV-1..10 协同：本 PR 不能破坏现有 invariants
- [ ] 确认 scope 生命周期的所有状态（creating / active / compacting / archiving / archived / failed）

## 实施 Checklist

### 1. 枚举

```python
class ScopeState(str, Enum):
    CREATING   = "creating"
    ACTIVE     = "active"
    COMPACTING = "compacting"
    ARCHIVING  = "archiving"
    ARCHIVED   = "archived"      # terminal
    FAILED     = "failed"         # terminal

ALLOWED = {
    ScopeState.CREATING:   {ScopeState.ACTIVE, ScopeState.FAILED},
    ScopeState.ACTIVE:     {ScopeState.COMPACTING, ScopeState.ARCHIVING, ScopeState.FAILED},
    ScopeState.COMPACTING: {ScopeState.ACTIVE, ScopeState.ARCHIVING, ScopeState.FAILED},
    ScopeState.ARCHIVING:  {ScopeState.ARCHIVED, ScopeState.FAILED},
    ScopeState.ARCHIVED:   set(),
    ScopeState.FAILED:     set(),   # manual recovery only
}
```

### 2. meta.json

- [ ] 写入 scope 时加 `state: "creating"` 初始
- [ ] 读取 scope 时 fallback `meta.get("state", "active")`（旧 scope 无此字段）

### 3. 唯一转移入口

- [ ] `scope_state.transition(scope_id, *, to, reason)`：
  - 在 scope 锁保护下读 meta → 校验 `ALLOWED` → 写入 meta → log + metric
- [ ] 所有以前散落的 "write meta.state" 改走 transition

### 4. 调用点

- [ ] scope.init 完成 → `transition(... to=ACTIVE, reason="init")`
- [ ] compact 开始/结束 → `COMPACTING ↔ ACTIVE`
- [ ] scope.end 开始 → `ARCHIVING`；归档完成 → `ARCHIVED`
- [ ] 任一无法恢复的错误 → `FAILED`

### 5. 与 INV 的协同

- [ ] INV-5（scope_end 幂等）：转移到 `ARCHIVED` 时，若已 `ARCHIVED` → silent no-op
- [ ] INV-6（方向性）：禁止 `ARCHIVED → ACTIVE`；CI lint

## 测试 Checklist

- [ ] 单测：合法转移链路
- [ ] 单测：非法转移 raise
- [ ] 集成：scope_end 调两次 → 第二次不报错，meta.state 最终 ARCHIVED

## 可观测性 Checklist

- [ ] metric `scope_transitions_total{from, to, reason}` counter
- [ ] log：`scope_state scope=... <from> -> <to> reason=...`

## 文档 Checklist

- [ ] [message-wake-refactor.md](../message-wake-refactor.md) P5-2 → `[x]`
- [ ] 本工单 Status → `[x]`
- [ ] [cortex/invariants.md](../../cortex/invariants.md) 加引用本 PR 作为 INV-5/6 的实现
- [ ] [cortex/scope-lifecycle.md](../../cortex/scope-lifecycle.md) 更新状态图

## 验收命令

```bash
cat ~/.novaic/cortex/scopes/<id>/meta.json | jq '.state'
# 预期：某个枚举值

rg 'meta.*"state"' novaic-cortex/novaic_cortex/ | rg -v 'scope_state.py|tests/'
# 预期：空（没有散落写入）
```

## 回滚

`git revert` —— 回到 "状态靠多字段推断"。

## 备注

- 此 PR 会让 PR-25 `/trace` 端点的 `scope.state` 字段真实化（之前只能是 derived）。
- `FAILED` 终态是故意的：手工 recovery 应当创建新 scope，不恢复老的。

## 实施总结（2026-04-15）

务实裁剪：今天 Cortex `meta.json` 里只出现两个 phase 值（`executing` / `archived`），没有 `creating` / `archiving` 这种中间态。引入 6 个状态会创造一堆没人写的 dead code，于是先按"现实状态 + 预留枚举"落地，把方法论搭好，等真有人需要 `compacting` / `failed` 再扩 `ALLOWED`。

### 代码

- `novaic-cortex/novaic_cortex/scope_state.py` —— 新模块：
  - `ScopeState` enum (`EXECUTING` / `COMPACTING` / `ARCHIVED` / `FAILED`)
  - `ALLOWED` 矩阵 + `InvalidScopeTransition` exception
  - `transition(workspace, scope_path, *, to, reason, actor, extra)` —— 唯一写入口
  - `mark_archived` 便捷封装（自动注入 `ended_at`）
  - `initial_phase()` —— `create_scope` 写初始值的"白名单"入口
  - 模块级 `Counter` + `dump_transition_counters()`
- `novaic-cortex/novaic_cortex/workspace.py`:
  - `create_scope` 用 `initial_phase()` 替代字符串字面量
  - `complete_child_scope` 走 `mark_archived(reason="scope_end_child")`
  - `archive_root_scope` 走 `mark_archived(reason="scope_end_root")`

### 不变量映射

- **INV-5（scope_end 幂等）**：自环 `ARCHIVED -> ARCHIVED` 在 `transition()` 内识别为 noop，不 bump metric，但仍允许写 `extra`（让重试刷新 `ended_at`）。
- **INV-6（archival 方向性）**：`ARCHIVED` 的 out-set 是空集，`ARCHIVED -> EXECUTING` 在矩阵层硬性拒绝。

### 测试

- `novaic-cortex/tests/test_scope_state.py` —— 16 个用例：合法转移、终态、自环幂等、`extra` 校验、缺 `phase` 字段的旧 scope 兼容、metric key 形状、workspace 集成。

### CI lint

- `scripts/ci/lint_scope_phase.sh` —— 禁止任何文件（除 `scope_state.py` / `workspace.py` / `tests/` / `docs/`）出现 `meta["phase"] = ...` 或 `"phase": "archived"` 这类直写。已挂到 `.github/workflows/lint.yml` 的 lint job。

### 验收

- 单测全绿（16/16）
- 全量 cortex 测试集相对 main 没有新增失败（21 个失败均为 main 上已有的 `/rw/active/` ↔ `/ro/active/` 路径漂移问题，与本 PR 无关）
- lint 在裸 repo 上 OK
