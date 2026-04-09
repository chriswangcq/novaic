# Compactor 与 Gem Fusion

> 源码：`novaic_cortex/compactor.py`（**`Compactor`**）。与 [scope-lifecycle.md](scope-lifecycle.md) 中的 **`archive_root_scope` / `complete_child_scope`** 衔接。

## 1. `compact(scope_id, report, scope_path, is_root)`

1. **`read_step_index(scope_path)`**（默认 **`/ro/active/{scope_id}`**）得到时间线。  
2. **`_build_summary_context(step_index)`**：把索引压成可读文本（tool/子 scope 行摘要），供 LLM 摘要或占位统计。  
3. **摘要正文 `summary`** 来源优先级：  
   - 调用方传入的 **`report`**；  
   - 否则若配置了 **`summarizer`** → 调 **`summarizer.summarize(context, max_tokens=...)`**；  
   - 否则生成 **无 LLM** 的 Markdown 占位（步数、tool/子 scope 计数）。  
4. **`is_root=True`**：**`archive_root_scope(scope_id, summary)`** → 树移到 `/ro/scopes/` 并写全局 `_index.jsonl`。  
5. **`is_root=False`**：**`complete_child_scope(scope_path, summary)`** → 子 scope 原地 **`summary.md` + meta archived**。  
6. **根归档后**：**`_maybe_fuse_gem()`**（见 §3）。  
7. 返回 **`CompactResult`**（`scope_id`、`summary`、`archive_path`）。

---

## 2. 与 `skill_end` 的关系

**`Cortex.skill_end`**（`runtime.py`）会调 **`compactor.compact`**（子 scope / 根 scope 由调用约定决定，见代码中 `is_root` 与 `scope_path`）。

---

## 3. Gem Fusion（`_maybe_fuse_gem` → `_fuse_at_level`）

- **开关**：**`gem_fusion_enabled`**、**`fusion_factor`（merge factor）**、**`gem_fusion_max_level`**（对应 **`EngineConfig`** 字段）。  
- **触发时机**：仅在 **`compact` 且 `is_root=True`** 归档成功之后。  
- **L1**：在 **`/ro/scopes/`** 下收集**根 scope 目录名**（排除 **`__fused__`**）。当 **根数量 `n` 为 `fusion_factor` 的整数倍** 且批次未跑过时，取 **`ended_at` 排序后最后 `fusion_factor` 个** 根的 **`summary.md`**，拼成一个大 **`summary.md`**，写到  
  **`/ro/scopes/__fused__/fuse_L1_{seq}/`**，并写 **`meta.json`**（`level: 1`, `children_ids`）。  
- **L2+**：从 **`__fused__/fuse_L{prev}_*/`** 再按批融合，生成 **`fuse_L{level}_{seq}`**，逻辑类似（读子 fused 的 `summary.md`）。  
- **指标**：`**_metrics.total_fusions**`、`**max_fusion_level**`；日志 **`log_cortex("fusion.triggered", ...)`**。

> **注意**：Recall（[recall.md](recall.md)）读的是 **`/ro/scopes/_index.jsonl` 里 depth==0 的「真实 scope」**；**`__fused__` 节点是否参与 Recall** 取决于索引是否单独写入——当前实现中 fusion 主要落在 **`__fused__`** 树，与 Recall 根表是**不同路径**，具体产品行为以 **`recall.py`** 是否扩展为准。

---

## 相关

- [scope-lifecycle.md](scope-lifecycle.md) — 归档  
- [engine-config-and-metrics.md](engine-config-and-metrics.md) — `gem_fusion_*` 配置  
- [recall.md](recall.md) — 记忆索引  
