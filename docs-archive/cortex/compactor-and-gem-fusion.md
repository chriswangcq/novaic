# Retired: Compactor 与 Gem Fusion

> PR-74 后，`novaic_cortex/compactor.py`、LLM 自动摘要器接线、Gem Fusion 写入路径均已删除。

本文保留为历史墓碑，避免旧链接断裂。

## 当前边界

Cortex 只负责两件事：

1. 维护 LIFO scope 树。
2. 按 scope 树拼装 LLM context。

`summary.md` 只有一个生产路径：

```text
LLM 显式 skill_begin(child_scope_id=...)
→ LLM 显式 skill_end(child_scope_id=..., report=...)
→ Cortex 将 report 原样写为该 child scope 的 summary.md
→ 后续 agent-root DFS 折叠该 child scope
```

结构性 `scope_end` 只归档生命周期容器，不生成、不推断、不保留传入 report 为 durable summary。

## 已删除内容

- `Compactor.compact(...)`
- `Summarizer` 注入协议
- `auto_summary_max_tokens`
- `gem_fusion_*` 配置
- `/ro/scopes/__fused__/...` 生成逻辑
- `total_fusions`、`max_fusion_level`、`total_tokens_saved`、`compactions_completed` 指标

## 相关

- [scope-lifecycle.md](scope-lifecycle.md)
- [context-timeline-and-dfs.md](context-timeline-and-dfs.md)
- [engine-config-and-metrics.md](engine-config-and-metrics.md)
