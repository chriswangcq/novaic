# 数据归属：Entangled、Gateway、Cortex、Queue

> 对应 `**HANDOVER.md` §12.2、§12.6**。**schema v63** 以 `novaic-gateway/gateway/db/schema.py` 为准。

## 总原则

- **用户消息 / Agent / SubAgent 等业务行**的权威存储在 **Entangled Service**（SQLite），经 Gateway `MessageRepository` 等写入；**不是** `gateway.db` 里的已删除业务表。
- **Gateway `gateway.db`**（v63）保留 **运维/运营** 表：`config`、`entangled_sync_versions`、`pending_questions`、`ssh_keys`、`vm_processes`、`pc_clients`、`subagent_context` 等。
- 历史上 `**agents` / `chat_messages` / `subagents` 等 shadow 表已 DROP**（见 `_SHADOW_AND_DEAD_TABLES`）。

## 消息写入路径（概念）

```
用户发消息
  → Gateway MessageRepository → Entangled `messages`（sending 等）
  → Watchdog → MessageProcess Saga → … → ReactThink（见 agent-pipeline.md）
```

若文档仍写「Gateway 本地 `chat_messages` INSERT」，应按 **v63** 理解：**进程在 Gateway**，**持久化在 Entangled**。历史对照文檔见 `[historical-doc-links.md](../historical-doc-links.md)`（`architecture-verification-2026-04`）。

## 数据分布表


| 数据                       | 权威位置                            |
| ------------------------ | ------------------------------- |
| 消息 / Agent / SubAgent 业务 | Entangled                       |
| Gateway 运维表              | `gateway.db`                    |
| Task / Saga              | Queue Service                   |
| 上下文 / Workspace / steps  | **Cortex**（S3，默认 HTTP `:19996`） |


## 相关

- [agent-pipeline.md](agent-pipeline.md) — Saga 与 Runtime  
- [cortex.md](cortex.md) — Cortex 存储模型

