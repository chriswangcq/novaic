# PR-09  `TriggerType` 权威枚举 + schema 迁移

| 字段 | 值 |
| --- | --- |
| **Phase** | 1 |
| **Milestone** | M1 |
| **承诺** | R2 |
| **Status** | `[x]` |
| **Depends on** | PR-01 |
| **Blocks** | PR-10 |
| **估时** | 0.5 d（+ 生产数据迁移） |
| **Owner** | __ |
| **PR 标题** | `feat(common): TriggerType enum + wake_triggers schema migration` |

## 目标

统一 `trigger_type` 取值，消除 `user_response` vs `user_message` 的枚举漂移。权威枚举放在 `common.wake.trigger_types`，schema `wake_triggers` 与代码同构。

## 范围

- `novaic-common/common/wake/trigger_types.py`（PR-01 占位，此处实装）
- `novaic-entangled/<schema>/subagents.json`（`wake_triggers` 默认值）
- 迁移脚本 `scripts/migrations/2026-XX-XX-wake-triggers-rename.sql`
- 全仓字符串替换（`'user_response'` → `'user_message'`）

## 前置 Checklist

- [x] `rg "'user_response'" novaic-*/' > /tmp/trig.txt` — 清点
- [x] `sqlite3 ~/.novaic/data/entangled.db "SELECT COUNT(*) FROM subagents WHERE wake_triggers LIKE '%user_response%';"` — 统计待迁移行数
- [x] **备份生产 Entangled DB**

## 实施 Checklist

### 1. 枚举定义

```python
# common/wake/trigger_types.py
from enum import Enum

class TriggerType(str, Enum):
    USER_MESSAGE    = "user_message"
    SUBAGENT_SEND   = "subagent_send"
    SPAWN_SUBAGENT  = "spawn_subagent"
    SCHEDULED_WAKE  = "scheduled_wake"
    SYSTEM_WAKE     = "system_wake"
    RECOVERED       = "recovered"        # 仅 HealthWorker / recovery_worker 使用

    @classmethod
    def from_legacy(cls, s: str) -> "TriggerType":
        """Back-compat for stored `user_response`."""
        mapping = {"user_response": cls.USER_MESSAGE}
        if s in mapping: return mapping[s]
        return cls(s)
```

- [x] 添加上述枚举
- [x] `__all__ = ["TriggerType"]`

### 2. Schema 迁移

- [x] Entangled schema push：`subagents.wake_triggers` 默认值从 `[{"type": "user_response"}]` 改为 `[{"type": "user_message"}]`
- [x] Schema 版本号 +1
- [x] 迁移 SQL：
  ```sql
  UPDATE subagents
     SET wake_triggers = REPLACE(wake_triggers, '"user_response"', '"user_message"')
   WHERE wake_triggers LIKE '%user_response%';
  ```
- [x] 迁移脚本幂等（多次执行结果不变）

### 3. 代码迁移

- [x] 所有业务代码中 `"user_response"` 字面量替换为 `TriggerType.USER_MESSAGE.value`
- [x] `trigger_type` 参数类型收紧（Pydantic 模型用 `TriggerType`，接收端用 `TriggerType.from_legacy` 宽容解析）
- [x] Queue Service `DispatchRequest.trigger_type` 也收紧为 `TriggerType`

### 4. 前端/其它 Client

- [x] Rust / TS 端若硬编码 `"user_response"` → 一并改
- [x] App config 若硬编码 → 一并改

## 测试 Checklist

- [x] 单测：`TriggerType.from_legacy("user_response") is TriggerType.USER_MESSAGE`
- [x] 迁移脚本：在一份拷贝 DB 上跑一次；再跑一次；结果幂等
- [/] 端到端：新建 subagent → `wake_triggers` 默认 `[{"type": "user_message"}]`（手工验证）

## 可观测性 Checklist

- [x] metric `dispatch_total{trigger_type=user_message|subagent_send|...}`（PR-10 会用到，这里先确保标签空间闭合）

## 文档 Checklist

- [x] [message-wake-refactor.md](../message-wake-refactor.md) P1-4 → `[x]`
- [x] 本工单 Status → `[x]`
- [x] 在 [message-wake-principles.md](../../architecture/message-wake-principles.md) §R2 里把枚举取值列清楚（当前已列出，核对一致）

## 验收命令

```bash
rg "'user_response'" novaic-*/ | rg -v "tests/|from_legacy|migrations/"
# 预期为空

sqlite3 ~/.novaic/data/entangled.db \
  "SELECT COUNT(*) FROM subagents WHERE wake_triggers LIKE '%user_response%';"
# 预期 0
```

## 回滚

- 代码 revert 可以；
- **Schema 迁移不可逆**（字符串已替换），但语义等价，所以实际上无需回滚 DB；
- 若必须回滚：用 SQL `REPLACE(..., 'user_message', 'user_response')` 反向执行。

## 备注

- 这是少数涉及**生产数据**的 PR，**单独合并、单独观察**至少 24h 再推 PR-10。
- `RECOVERED` 不由上游产生，仅 recovery_worker 在 re-dispatch 时打；有它是为了 metric 上和主路径分开。
