# PR-01 Review — `common.wake` 包骨架

> **工单**：[PR-01-wake-package-skeleton.md](../PR-01-wake-package-skeleton.md)
> **Reviewer**：__
> **Reviewee**：__
> **结论**：`[~] 返工`。骨架能 import、能过验收命令，但因为照着 ticket 字面执行而**在仓库里凭空多出一个顶层包 `novaic_common/`**，与现有顶层包 `common/` 并存。此问题若不修，PR-05/08/10 的 import 路径全部对不上，Phase 1 会被阻塞。

---

## 一、必须修的问题（返工项）

### 1. 包名错位（致命）

**现状**：

```
novaic-common/
├── common/              ← 现有（所有业务代码：http/clients.py、auth.py、config.py 等）
└── novaic_common/       ← 🆕 你新建的第二个顶层包
    └── wake/
```

**修法**：

- 把 `novaic-common/novaic_common/` 整个 **迁移** 到 `novaic-common/common/wake/`（保留你写的 `assembler.py` / `trigger_types.py` / `errors.py`）
- 删除 `novaic-common/novaic_common/` 顶层目录（包括 `novaic_common/__init__.py` 和 `wake/__pycache__/`）
- 确认 `common/__init__.py` 现有内容（`from .exceptions import ...`）不受影响；**不要**去改它

**验证**：

```bash
cd novaic-common
test ! -d novaic_common         # 不存在
test -d common/wake             # 存在
python -c "from common.wake import DispatchError, AgentNotOwnedError; print('OK')"
python -c "from common.wake.assembler import DispatchAssembler; print('OK')"
python -c "from common.wake.trigger_types import TriggerType; print('OK')"
# 同时确认现有代码没被搞坏：
python -c "from common.http.clients import internal_client; print('OK')"
python -c "from common.auth import *; print('OK')" 2>&1 | head -3
```

> 责任划分：ticket 原版里把路径写成 `novaic_common.*` 是 reviewer 的 bug（已在所有 PR-0x/PR-1x 工单中批量改回 `common.*`）。但你**看到一个 ticket 要新建顶层包时，没有 `ls` 一下现有仓库核对**——这是工程师的基本嗅觉。下次遇到"新建包/新建模块"类任务，**第一件事永远是 `ls` + `rg` 确认**现有结构。

### 2. `__init__.py` 的 namespace 注释矛盾

**现状**（`novaic_common/__init__.py`）：

```python
# namespace package
```

**问题**：

- PEP 420 的 namespace package 定义是 "**没有** `__init__.py`"。
- 你写了 `__init__.py` 并留这条注释，实现与注释**直接矛盾**。
- 同时，这个 `__init__.py` 因为错误的顶层包也要被删（回到第 1 点），连带着注释问题自然消失。

**修法**：

- 删掉该文件（随第 1 条一起处理）
- **理解原因**：regular package（有 `__init__.py`，可放逻辑）vs namespace package（没 `__init__.py`，纯聚合）——下次写注释前先查一下 PEP。

### 3. `wake/__init__.py` 的 `__all__` 语义问题

**现状**：

```python
from .errors import DispatchError, AgentNotOwnedError

__all__ = []
```

**问题**：

- 既然 re-export 了两个符号，`__all__ = []` 会让 `from common.wake import `* **拿不到它们**——与你的 re-export 初衷矛盾。
- ticket 占位原文只说"`__all__ = []`"是因为 ticket 写的时候没考虑 re-export；你选择 re-export 是对的，但 `__all__` 要同步。

**修法**：

```python
"""SSOT: docs/architecture/message-wake-principles.md (R2).

Public entry point is DispatchAssembler (PR-10).
"""

from .errors import DispatchError, AgentNotOwnedError

__all__ = ["DispatchError", "AgentNotOwnedError"]
```

### 4. 占位类缺 docstring

**现状**：

```python
class DispatchAssembler:
    def __init__(self):
        raise NotImplementedError("Implemented in PR-10")
```

**修法**：

```python
class DispatchAssembler:
    """Single entry point for wake dispatches (placeholder).

    Implemented in PR-10. See
    docs/architecture/message-wake-principles.md §R2.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Implemented in PR-10")
```

同样方式补 `TriggerType`。把 `__init__` 签名改 `*args, **kwargs` 而不是裸 `self`，避免给调用方误导"无参"。

### 5. 未 commit（工程规范）

**现状**：`git status` 显示 `?? novaic_common/`——改动未 commit。

**修法**：

- 返工完成后：
  ```bash
  cd novaic-common
  git add common/wake/
  git status         # 确认只有 wake/ 下的新文件，novaic_common/ 不在
  git commit -m "feat(common): common.wake package skeleton (PR-01)"
  git push origin main
  ```
- 回到主仓：
  ```bash
  cd ..
  git add novaic-common
  git commit -m "chore: bump novaic-common for PR-01 wake skeleton"
  ```
- 在 PR 描述里贴你跑过的验收命令输出

**原则**：**没 commit 就不算完成**。以后每个工单的最后一步固定就是 commit + push。

---

## 二、做得对的地方

- SSOT docstring 到位
- `errors.py` re-export 得干净
- 验收命令（`python -c "import ..."` ）能跑通
- 按 ticket 分文件不混写，没把逻辑提前塞进占位

---

## 三、工程习惯反馈（下次怎么做得更好）


| 维度               | 这次表现                                                | 下次期望                                                |
| ---------------- | --------------------------------------------------- | --------------------------------------------------- |
| **前置核对**         | 未核对就动手                                              | 开工前 5–10 min `ls` + `rg` 对每条"新增路径"做 reality check   |
| **异议回报**         | 全盘接受 ticket                                         | 发现与现实不符时，**在开工前** 先回一句 "ticket 说 X，但仓库里是 Y，确认按哪个做？" |
| **checklist 诚信** | 把没做的 "前置 checklist" 勾了 `[x]`（如 `pyproject.toml` 那条） | 没做就 `[ ]` 或 `[!]`（已确认无需做并说明为什么）                     |
| **交付闭环**         | 忘记 commit + push                                    | 每个工单最后一步固定 commit + push；PR 描述里贴验收命令输出              |


**要背下的三条**：

1. **Code 前先 Read**：任何"新建文件/新建包"的动作，先 `ls`/`rg` 现有结构。
2. **有疑必问**：ticket 和仓库不一致时**停下来回报**，不自己发明。
3. **无 commit 即无 PR**：工单最后一行永远是 commit + push。

---

## 四、返工验收 Checklist（你要逐条勾）

- `novaic-common/novaic_common/` 不复存在
- `novaic-common/common/wake/` 存在，含 4 个文件（`__init__.py`, `assembler.py`, `trigger_types.py`, `errors.py`）
- `__init__.py` 的 `__all__ = ["DispatchError", "AgentNotOwnedError"]`
- `assembler.py` / `trigger_types.py` 占位类有 docstring，`__init__` 签名 `(*args, **kwargs)`
- `from common.wake import DispatchError, AgentNotOwnedError` 跑通
- `from common.wake.assembler import DispatchAssembler` 跑通
- `from common.http.clients import internal_client` 跑通（确认没把现有 `common/` 搞坏）
- `git status` 干净（没有 `??`）
- novaic-common 子仓的 commit 已 push 到 origin/main
- 主仓的子模块指针 bump commit 已就位
- 本 review 在 PR 描述里被引用

---

## 五、是否接着干下一单

**可以**，继续按工单顺序：

- **PR-02**（common.agents.ownership 骨架）——同类任务，这是你第二次机会证明前置核对做得到
- **PR-03 / PR-04**（CI lint 规则）——任务边界清晰，是独立 PR，合适给你

**暂不接**：PR-05（internal_client 升级，跨多个子仓）、PR-10（Assembler 本体，关键 PR）。做完 PR-02/03/04 稳定后再评估。

**开工 PR-02 前必交付的"前置调研回报"**（10 分钟内写完发 reviewer）：

1. `novaic-common/common/agents/` 目录存不存在？`common/` 下已有 `agents`、`auth`、`http` 之类的哪些子包？
2. 现有代码里有没有 `get_agent_owner` / `agent_owner` / `user_id` 之类的函数？
3. 你打算新增哪几个文件，分别多长？
4. ticket 里有没有任何一句和现实不符？

**这份回报收到前，不要动代码。**