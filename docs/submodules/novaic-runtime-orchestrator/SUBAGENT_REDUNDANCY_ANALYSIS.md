# subagent.py 冗余分析

> 针对 `gateway/api/internal/subagent.py` 保留路由的进一步冗余分析。

---

## 一、未使用的导入

| 导入 | 使用情况 |
|------|----------|
| `resolve_runtime_ids` | **未使用**（runtime.py 使用，subagent.py 不用） |
| `get_runtime_context` | **未使用**（runtime.py 使用） |
| `_runtime_to_dict` | **未使用**（subagent 路由不返回 runtime） |
| `Query` (from fastapi) | **未使用** |
| `json` | **未使用** |
| `Optional`, `List`, `Tuple` | 仅 docstring 提及，无类型注解使用 |
| `datetime` | 顶部已导入，`get_subagent_status` 内重复导入 |

**建议**：移除未使用导入，删除 `get_subagent_status` 内重复的 `from datetime import datetime`。

---

## 二、maybe_forward_to_runtime_orchestrator（已删除）

**2025-03 已执行**：已从 runtime.py、subagent.py 移除所有 `maybe_forward_to_runtime_orchestrator` 调用，并从 helpers.py 删除该函数及 `set_runtime_orchestrator_process`。RO 仅本地执行，无代理逻辑。

---

## 三、get_subagent_status 的 spawn 遗留逻辑

| 逻辑 | 说明 |
|------|------|
| **timeout 检查** | 原为 async spawn 设计：`timeout_at` 过期则 `set_failed` |
| **docstring** | 仍写 "Get SubAgent status for async spawn polling" |
| **spawn 已删除** | 不再创建带 `timeout_at` 的 subagent |

**建议**：
- **保守**：保留 timeout 逻辑（防御历史数据）
- **激进**：删除 timeout 分支，简化实现，并更新 docstring

---

## 四、helpers 依赖

`subagent.py` 从 helpers 导入：
- `_subagent_to_dict` ✓ 使用
- `maybe_forward_to_runtime_orchestrator` 已删除
- `resolve_runtime_ids`, `get_runtime_context`, `_runtime_to_dict` ✗ 未使用

---

## 五、可执行清理项（低风险）

1. 移除未使用导入：`resolve_runtime_ids`, `get_runtime_context`, `_runtime_to_dict`, `Query`, `json`
2. 移除 `get_subagent_status` 内重复的 `from datetime import datetime`
3. 精简 typing 导入：仅保留 `Dict`, `Any`（若其他未用）
4. 更新 `get_subagent_status` docstring，去掉 "async spawn polling"
