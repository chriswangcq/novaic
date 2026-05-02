# 数据归属：Entangled、Gateway、Cortex、Queue

> 与当前 schema 一致；对应原 **`HANDOVER.md` §12.6**。**schema v63**：`novaic-gateway/gateway/db/schema.py`。

## 总原则

- **用户消息 / Agent / SubAgent 等业务行** 权威在 **Entangled Service**（SQLite）；经 Business Service 写入（via Entangled HTTP）。
- **`gateway.db`** 保留 **运维** 表：`config`、`entangled_sync_versions`、`pending_questions`、`question_responses`、`ssh_keys`、`vm_processes`、`pc_clients`、`subagent_context` 等。
- **`agents` / `subagents` / `chat_messages` 等** 在 **`_SHADOW_AND_DEAD_TABLES`** 中 **已 DROP**（勿再当作业务主表）。

## 消息路径（与持久化）

```
用户发消息
  → Gateway → Business Environment IM event + chat UI projection
  → Environment notification → DispatchSubscriber → Queue/Saga/Runtime（见 agent-pipeline.md）
```

若他处仍写「Gateway 本地 `chat_messages` INSERT」或「Business outbox」：那是旧文档口径，不是当前控制流。

## 数据分布表

| 数据 | 权威位置 | 说明 |
|------|----------|------|
| 用户消息 / Agent / SubAgent **业务行** | **Entangled** | 经 Business → Entangled |
| Gateway `gateway.db` | **运维表 only** | v63 见 `schema.py` |
| Task / Saga | Queue Service | `tasks`, `sagas` |
| Workspace / 上下文 | **Cortex**（S3，HTTP 默认 19996） | scope、steps 等 |

## 相关

- [agent-pipeline.md](agent-pipeline.md)  
- [cortex.md](cortex.md)  
