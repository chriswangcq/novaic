# PR-01  `common.wake` 包骨架

| 字段 | 值 |
| --- | --- |
| **Phase** | M0（工程卫生） |
| **Milestone** | M1（前置） |
| **承诺** | R2 |
| **Status** | `[x]` |
| **Depends on** | — |
| **Blocks** | PR-08, PR-09, PR-10 |
| **估时** | 0.5 h |
| **Owner** | __ |
| **PR 标题** | `feat(common): common.wake package skeleton` |

## 目标

建立空包，让后续 PR 有地方落代码；同时确立"所有 dispatch 相关模块只在这个包里"的唯一来源。

## 范围 (Scope)

新建文件：
- `novaic-common/common/wake/__init__.py`
- `novaic-common/common/wake/assembler.py`
- `novaic-common/common/wake/trigger_types.py`
- `novaic-common/common/wake/errors.py`

## 前置 Checklist

- [x] `novaic-common` submodule 干净、在 `main` 分支
- [x] 确认 `common` 包的 `pyproject.toml` / `setup.py` 包含通配安装子包

## 实施 Checklist

- [x] `__init__.py`：暴露占位 `__all__ = []`，注释 "Public entry point is `DispatchAssembler` (PR-10)."
- [x] `assembler.py`：空 `class DispatchAssembler: ...` + `raise NotImplementedError("Implemented in PR-10")`
- [x] `trigger_types.py`：空 `class TriggerType: ...` + NotImplementedError 占位（PR-09 填充）
- [x] `errors.py`：
  ```python
  class DispatchError(Exception):
      """Raised by DispatchAssembler. See PR-10 for kinds."""
  class AgentNotOwnedError(Exception):
      """Raised by AgentOwnershipResolver when agent has no owner. See PR-08."""
  ```
- [x] 所有文件头加 `"""SSOT: docs/architecture/message-wake-principles.md (R2)."""` docstring

## 测试 Checklist

- [x] `python -c "import common.wake; from common.wake import DispatchError, AgentNotOwnedError"` 无 ImportError
- [x] 无单测（纯骨架）

## 可观测性 Checklist

- n/a

## 文档 Checklist

- [x] 在本工单 `Status` 改为 `[x]`
- [x] 在 [tickets/README.md](README.md) 对应行改为 `[x]`

## 验收命令

```bash
cd novaic-common && python -c "
from common.wake import DispatchError, AgentNotOwnedError
from common.wake import assembler, trigger_types
print('OK')
"
```

预期输出：`OK`

## 回滚

`git revert <sha>` — 纯新增文件，不影响任何现有代码。

## 备注

- 本 PR 只定义占位，**不**要提早实现 Assembler 逻辑（那是 PR-10 的事），否则会让 PR 合并顺序变复杂。
