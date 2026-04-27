# 可观测性与测试布局

> 源码：`novaic_cortex/observability.py`；各模块 `logging.getLogger(__name__)`；测试目录 **`novaic-cortex/tests/`**。

## 1. `log_cortex(event, **kwargs)`

- **logger**：**`novaic_cortex`**（INFO）。  
- 格式：**`[CORTEX] {event}`** 后接 **`k=v`**，每个值 **`repr` 截断 200 字符**。  
- 典型 **event**（见 `observability.py` 注释）：`scope.created`、`scope.archived`、`sandbox.exec`、`recall.generated` 等。

业务逻辑中在关键路径调用 **`log_cortex`**，与普通模块 logger 并存。

---

## 2. 测试（`tests/`）

目录为**扁平**结构，按模块命名，例如：

| 前缀 / 文件名模式 | 大致覆盖 |
|-------------------|----------|
| `test_workspace*.py` | Workspace、路径、scope |
| `test_sandbox*.py` | `Sandbox.exec`、回写 |
| `test_recall*.py` | `Recall` |
| `test_context_budget*.py` | `usage_ratio`、`compact_level` 等 |
| `test_engine*.py` | `ContextEngine` 与预算 |

**`ContextEngine`** 也常通过 **HTTP** 与配置/budget **间接**覆盖；以实际测试文件为准。

---

## 相关

- [engine-config-and-metrics.md](engine-config-and-metrics.md) — metrics 类型  
