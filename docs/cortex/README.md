# Cortex 专题文档

源码目录：**`novaic-cortex/novaic_cortex/`**。总览见 **[../cortex-architecture.md](../cortex-architecture.md)**。

---

## 按主题

| 文档 | 内容 |
|------|------|
| [scope-lifecycle.md](scope-lifecycle.md) | 根/子 scope、`/ro/active` 与 `/ro/scopes`、归档、`meta.json`、统一时间线写入 |
| [context-timeline-and-dfs.md](context-timeline-and-dfs.md) | `ContextEngine`、`steps/_index.jsonl`、DFS 展开与折叠、`budget_compact` |
| [recall.md](recall.md) | `Recall`、`/ro/scopes/_index.jsonl`、与 session `meta` 中 recall 的关系 |
| [storage-and-keys.md](storage-and-keys.md) | `CortexStore`、`WorkspaceRegistry`、`Workspace._key` 与完整 S3 前缀 |
| [sandbox-shell.md](sandbox-shell.md) | `Sandbox.exec`：物化、`NOVAIC_TOKEN`、与 VM/proxy shell 的区别 |
| [compactor-and-gem-fusion.md](compactor-and-gem-fusion.md) | `Compactor.compact`、归档、`__fused__`、gem fusion 批次 |
| [engine-config-and-metrics.md](engine-config-and-metrics.md) | `EngineConfig`、`/ro/config/engine.json`、`budget_compact`、`CortexMetrics` |
| [runtime-facade.md](runtime-facade.md) | `Cortex` 门面：initialize、builtin tools、`skill_*` 与 compactor |
| [http-api.md](http-api.md) | `api.py` 全部路由：Agent / CLI / Internal 分层 |
| [proxy-cli-auth.md](proxy-cli-auth.md) | 能力 JWT、`GatewayProxy`、`novaic` CLI |
| [observability-and-tests.md](observability-and-tests.md) | `log_cortex`、`tests/` 布局 |

---

## 建议阅读顺序（学习路径）

1. **数据放哪、键长什么样** → [storage-and-keys.md](storage-and-keys.md)  
2. **scope 怎么活、怎么归档** → [scope-lifecycle.md](scope-lifecycle.md)  
3. **给 LLM 的上下文怎么从时间线拼出来** → [context-timeline-and-dfs.md](context-timeline-and-dfs.md)  
4. **记忆从哪来** → [recall.md](recall.md)  
5. **scope 结束摘要与可选融合** → [compactor-and-gem-fusion.md](compactor-and-gem-fusion.md)  
6. **窗口与压缩阈值** → [engine-config-and-metrics.md](engine-config-and-metrics.md)  
7. **shell 在本地盘跑一圈** → [sandbox-shell.md](sandbox-shell.md)  
8. **`Cortex` 类怎么串起来** → [runtime-facade.md](runtime-facade.md)  
9. **HTTP 入口一览** → [http-api.md](http-api.md)  
10. **JWT / Gateway / CLI** → [proxy-cli-auth.md](proxy-cli-auth.md)  
11. **日志与单测从哪找** → [observability-and-tests.md](observability-and-tests.md)  

（1–4 与第一版拆页一致；5–11 为第二版拆页，可按需跳读。）
