# PR-02  `common.agents.ownership` 包骨架

| 字段 | 值 |
| --- | --- |
| **Phase** | M0（工程卫生） |
| **Milestone** | M1（前置） |
| **承诺** | R3 |
| **Status** | `[x]` |
| **Depends on** | — |
| **Blocks** | PR-08 |
| **估时** | 0.5 h |
| **Owner** | __ |
| **PR 标题** | `feat(common): common.agents.ownership skeleton` |

## 目标

建立 `AgentOwnershipResolver` 的落地位置，不实现逻辑。

## 范围

新建：
- `novaic-common/common/agents/__init__.py`（若不存在）
- `novaic-common/common/agents/ownership.py`

## 前置 Checklist

- [x] 确认 `common.agents` 子包不存在或为空

## 实施 Checklist

- [x] `agents/__init__.py`：空文件（或 `"""Agent-related shared code (ownership, etc.)."""`）
- [x] `agents/ownership.py`：
  ```python
  """SSOT: docs/architecture/message-wake-principles.md (R3).

  Implementation lands in PR-08; this file only reserves the module path.
  """

  from common.wake.errors import AgentNotOwnedError  # re-export

  class AgentOwnershipResolver:
      def __init__(self, *args, **kwargs):
          raise NotImplementedError("Implemented in PR-08")
  ```

## 测试 Checklist

- [x] `python -c "from common.agents.ownership import AgentOwnershipResolver, AgentNotOwnedError"` 无 ImportError

## 文档 Checklist

- [x] 本工单 Status → `[x]`；README index → `[x]`

## 验收命令

```bash
cd novaic-common && python -c "
from common.agents.ownership import AgentOwnershipResolver, AgentNotOwnedError
print('OK')
"
```

## 回滚

`git revert` — 纯新增。

## 备注

- 依赖 PR-01 的 `errors.py`。若 PR-01 尚未合并，本 PR 可内嵌临时 `class AgentNotOwnedError(Exception)`，但推荐先合 PR-01。
