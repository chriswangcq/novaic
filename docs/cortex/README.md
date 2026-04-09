# Cortex 专题文档

源码目录：`**novaic-cortex/novaic_cortex/**`。总览见 `**[../cortex-architecture.md](../cortex-architecture.md)**`。


| 文档                                                         | 内容                                                                 |
| ---------------------------------------------------------- | ------------------------------------------------------------------ |
| [scope-lifecycle.md](scope-lifecycle.md)                   | 根/子 scope、`/ro/active` 与 `/ro/scopes`、归档、`meta.json`、统一时间线写入       |
| [context-timeline-and-dfs.md](context-timeline-and-dfs.md) | `ContextEngine`、`steps/_index.jsonl`、DFS 展开与折叠、`budget_compact`    |
| [recall.md](recall.md)                                     | `Recall` 类、`/ro/scopes/_index.jsonl`、与 session `meta` 中 recall 的关系 |


阅读顺序建议：**scope-lifecycle** → **context-timeline-and-dfs** → **recall**（三者有交叉引用）。