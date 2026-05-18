# Recall（历史/已退役）

> 这个页面只保留给考古。当前 `novaic-cortex/novaic_cortex/` 已没有 `recall.py` 源码，`api.py` 也不再暴露 `/v1/recall` 或 `/v1/internal/recall*` 路由。LLM 主路径不要再按本文旧设计理解系统行为。

## 当前事实

- 跨 wake 连续性来自 **agent-root scope 树**。
- 每个 wake 是 agent-root 下的一个 child scope。
- LLM 关闭 wake 或子 skill 时调用 `skill_end(report=...)`。
- `report` 原样写入该 scope 的 `summary.md`。
- 后续 `context.prepare_for_llm` 从 agent-root 做 DFS：开放 scope 展开，已关闭且有非空 `summary.md` 的 scope 折叠成 system message。

## 已删除的旧概念

- 独立 `Recall` 类扫描 `/ro/scopes/_index.jsonl` 注入长期记忆。
- `/v1/recall`、`/v1/internal/recall`、`/v1/internal/recall_messages`。
- 从历史 root scope、chat_reply 或工具结果自动拼 wake summary。
- `meta.recall_messages` 作为当前主路径的一部分。

## 保留这个页面的原因

旧票据和历史设计稿会引用 “Recall”。看到这些引用时，应把它理解为旧方案背景，不应作为当前实现或新开发的依据。当前实现以这些页面为准：

- [scope-lifecycle.md](scope-lifecycle.md)
- [context-timeline-and-dfs.md](context-timeline-and-dfs.md)
- [http-api.md](http-api.md)
- [../architecture/cortex.md](../architecture/cortex.md)
