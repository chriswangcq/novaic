# Cortex 专题文档

源码目录：**`novaic-cortex/novaic_cortex/`**。总览见 **[../cortex-architecture.md](../cortex-architecture.md)**。

---

## 按主题

| 文档 | 内容 |
| --- | --- |
| [scope-lifecycle.md](scope-lifecycle.md) | 根/子 scope、`/ro/active` 与 `/ro/scopes`、归档、`meta.json`、统一时间线写入；**§9 Skill scope 生命周期（scope_id 全局唯一、LIFO 严校验、Meta skill、瞬态栈快照）** |
| [step-index-and-payload-schema.md](step-index-and-payload-schema.md) | `steps/_index.jsonl` 行类型、tool/assistant/env/scope 与磁盘 JSON |
| [session-meta-json.md](session-meta-json.md) | `meta.json` 字段、`ContextEngine` 前缀、`/v1/meta/*` |
| [context-timeline-and-dfs.md](context-timeline-and-dfs.md) | `ContextEngine`、DFS 展开与折叠、`budget_compact` |
| [recall.md](recall.md) | `Recall`、`/ro/scopes/_index.jsonl`、与 session `meta` 中 recall 的关系 |
| [storage-and-keys.md](storage-and-keys.md) | `CortexStore`、`WorkspaceRegistry`、对象键 |
| [sandbox-shell.md](sandbox-shell.md) | `Sandbox.exec`、与 VM/proxy shell 的区别 |
| [compactor-and-gem-fusion.md](compactor-and-gem-fusion.md) | 已退役：`Compactor`、自动摘要、gem fusion |
| [engine-config-and-metrics.md](engine-config-and-metrics.md) | `EngineConfig`、`engine.json`、指标 |
| [budget-compact-algorithm.md](budget-compact-algorithm.md) | `budget_compact` 三档算法 |
| [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md) | `cortex.prepare_llm_context` 调用链 |
| [agent-runtime-all-topics.md](agent-runtime-all-topics.md) | Runtime 全部 Cortex topic、`context.append`、Saga |
| [runtime-facade.md](runtime-facade.md) | `Cortex` 门面、builtin tools、`skill_*` |
| [http-api.md](http-api.md) | `api.py` 路由分层 |
| [internal-api-schemas.md](internal-api-schemas.md) | Internal 路由请求/响应摘要 |
| [proxy-cli-auth.md](proxy-cli-auth.md) | 能力 JWT、`GatewayProxy`、`novaic` CLI |
| [proxy-gateway-routes.md](proxy-gateway-routes.md) | `/v1/proxy/{command}` → Gateway 路径 |
| [observability-and-tests.md](observability-and-tests.md) | `log_cortex`、`tests/` |
| [deployment-and-startup.md](deployment-and-startup.md) | `main_cortex`、OSS、`startup` |
| [workspace-acl-and-sys-writes.md](workspace-acl-and-sys-writes.md) | `/ro`/`/rw` ACL、`_sys_*` |
| [builtin-tools-and-skills.md](builtin-tools-and-skills.md) | 工具 schema、`install_skill` |
| [extension-points.md](extension-points.md) | Hooks、协议、StepTree、压缩建议 |
| [satellite-modules.md](satellite-modules.md) | Entangled、`fs://`、TRS 等 |
| [design-doc-links.md](design-doc-links.md) | 源码注释中的设计稿路径、历史文档 |
| [invariants.md](invariants.md) | **硬约束 SSOT**：10 条跨服务 invariants、代码锚点、强制级别 |
| [hardening-checklist.md](hardening-checklist.md) | Phase 0-3 加固清单 + 风险矩阵 |
| [architecture-review-2026-04-17.md](architecture-review-2026-04-17.md) | 8 位架构师评审 + 8 位 summarizer 汇总 |

---

## 建议阅读顺序（学习路径）

1. **数据放哪** → [storage-and-keys.md](storage-and-keys.md)  
2. **scope 生命周期** → [scope-lifecycle.md](scope-lifecycle.md)  
3. **时间线索引长什么样** → [step-index-and-payload-schema.md](step-index-and-payload-schema.md)  
4. **会话 meta** → [session-meta-json.md](session-meta-json.md)  
5. **拼 LLM 消息** → [context-timeline-and-dfs.md](context-timeline-and-dfs.md)  
6. **Recall** → [recall.md](recall.md)  
7. **压缩与配置** → [engine-config-and-metrics.md](engine-config-and-metrics.md) → [budget-compact-algorithm.md](budget-compact-algorithm.md)  
8. **Runtime 调用链** → [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md) → [agent-runtime-all-topics.md](agent-runtime-all-topics.md)  
9. **HTTP 与契约** → [http-api.md](http-api.md) → [internal-api-schemas.md](internal-api-schemas.md)  
10. **Proxy / Gateway** → [proxy-cli-auth.md](proxy-cli-auth.md) → [proxy-gateway-routes.md](proxy-gateway-routes.md)  
11. **其余专题** → [sandbox-shell.md](sandbox-shell.md)、[runtime-facade.md](runtime-facade.md)、[deployment-and-startup.md](deployment-and-startup.md)、[workspace-acl-and-sys-writes.md](workspace-acl-and-sys-writes.md)、[builtin-tools-and-skills.md](builtin-tools-and-skills.md)、[extension-points.md](extension-points.md)、[satellite-modules.md](satellite-modules.md)、[observability-and-tests.md](observability-and-tests.md)、[design-doc-links.md](design-doc-links.md)  

可按需跳读；**契约与排障**优先 **§3–4、§9–10**。
