# 设计文档与代码中的引用

Cortex 源码注释会指向一些 **`docs/...md`** 路径（如 **`docs/context-stack-v2-passive-design.md`**、**`docs/scope-driven-agent-lifecycle.md`**）。这些文件**未必**存在于当前父仓库 **`docs/`** 目录，可能位于：

- 历史提交：见父仓库 **[historical-doc-links.md](../historical-doc-links.md)**  
- 子模块或已归档树：`git show docs-graveyard-p2:docs/...` 等（以 **`historical-doc-links.md`** 为准）

**仍以源码与父仓库 `docs/cortex/*.md` 为行为准**；旧设计长文仅作背景。

---

## 与专题拆页的对应关系（非一一映射）

| 源码/旧稿常见标题 | 父仓专题（优先读） |
|------------------|-------------------|
| Context Stack v2 / budget §4.4 | [budget-compact-algorithm.md](budget-compact-algorithm.md)、[engine-config-and-metrics.md](engine-config-and-metrics.md) |
| DFS / 时间线 | [context-timeline-and-dfs.md](context-timeline-and-dfs.md)、[step-index-and-payload-schema.md](step-index-and-payload-schema.md) |
| OSS / `fs://` | [satellite-modules.md](satellite-modules.md)、父仓 `docs/oss-storage-unified-plan.md`（若存在） |

---

## 相关

- [historical-doc-links.md](../historical-doc-links.md)  
- [cortex-architecture.md](../cortex-architecture.md)  
