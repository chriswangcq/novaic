# Workspace：Agent ACL 与系统写

> 源码：`novaic_cortex/workspace.py`。

## 1. 两区模型（与纲要一致）

- **`/ro/**`：Cortex 管理（scopes、config、skills 等）。Agent **可读**（`read` / `list_dir` / `exists`），**不能**通过公开 `write` 写入。
- **`/rw/**`：Agent **可读写**（`write`、`append_line`、`delete` 等）。

## 2. 强制规则：`_validate_write`

所有 **Agent 侧写路径**（`write`、`write_bytes`、`write_json`、`append_line`、`delete`）在开头调用 **`_validate_write`**：

- 逻辑路径必须 **`strip()` 后以 `/rw/` 开头**，否则 **`PermissionError`**（`agent cannot write ... (only /rw/)`）。

**读**（`read` / `read_bytes` / `list_dir`）**不**做「仅 `/ro`」限制——可读 `/ro` 与 `/rw`。

## 3. 系统写：`_sys_*`（绕过 ACL）

Cortex 内部写 **`/ro/...`** 时使用：

| 方法 | 作用 |
|------|------|
| **`_sys_write`** | 文本写入 |
| **`_sys_write_json`** | JSON 对象写入 |
| **`_sys_append_line`** | 按行追加 |

这些方法**不**经过 `_validate_write`，直接 **`_key` → `store.put`**。

Scope 创建、步骤、归档、配置等路径均应走 **`_sys_*`**（或经同一 store 层的内部 API），保证 **`/ro`** 仅由服务写入。

## 4. `Workspace` 内 hooks

若构造时传入 **`CortexHooks`**，部分生命周期会通过 **`_emit`** 调用 hook 列表（与 `runtime.Cortex._fire_hook` 互补；见 **[extension-points.md](extension-points.md)**）。

---

## 相关

- [scope-lifecycle.md](scope-lifecycle.md)
- [object-keys.md](object-keys.md)
