# Cortex 认知引擎（当前架构摘要）

> 对应 **`HANDOVER.md` §18**。完整长文在历史树：[`historical-doc-links.md`](../historical-doc-links.md)（`cortex-architecture`、`context-assembly-dfs-step-tree`）。过时设计稿：`git show docs-graveyard-p2:docs/archived/`。

Cortex 为 **独立 HTTP 服务**（默认 **`19996`**），S3-backed，负责 Workspace、上下文拼装（**DFS Step Tree**）、Recall、Sandbox。

## 存储模型

| 区域 | 管理者 | Agent | 内容 |
|------|--------|-------|------|
| `/ro/` | Cortex | 只读 | `active/`、`scopes/`、`config/`、`skills/`、`knowledge/` 等 |
| `/rw/` | Agent | 读写 | `scratch/` |

Scope 为系统对象；创建/写 step/归档多用 **`_sys_*`**，绕过 `/rw/` ACL。

## DFS Step Tree（概念）

- **上下文原子单位是 step，不是 message。**
- Step：**tool**（叶）与 **scope**（复合）；索引见各 scope 下 `steps/_index.jsonl`。
- **闭合 scope** → 折叠为 summary；**开放** → DFS 展开子 step。
- **Tool 结果**主要在 `steps/` 文件；`context.jsonl` 偏非 step 类消息（见 HANDOVER §18.3）。

## 核心组件（novaic-cortex）

| 组件 | 职责 |
|------|------|
| `Workspace` | 文件抽象与 CRUD |
| `WorkspaceRegistry` | 多租户缓存 |
| `ContextEngine` | DFS 拼装 |
| `StepTreeBuilder` | 自 S3 建内存树 |
| `budget_compact` | token 预算压缩 |
| `Recall` | 归档 scope → system messages |
| Runtime 侧 `CortexBridge` | HTTP 客户端，不直接 import Cortex |

## Runtime 集成约定（摘要）

- `skill_begin` / `skill_end` 管理 scope 生命周期；其它工具结果多经 `POST /v1/steps/write`。
- Agent Runtime 经 **CortexBridge**（httpx）调 Cortex。

## 部署（本地/典型）

| 项 | 值 |
|----|-----|
| 端口 | `19996`（`CORTEX_PORT`） |
| 启动 | `python -m novaic_cortex.main_cortex` |
| 健康检查 | `GET /health` |

生产 S3/密钥见 HANDOVER §18.7 与子模块 README。

## 相关

- [data-ownership.md](data-ownership.md)  
- [agent-pipeline.md](agent-pipeline.md)  
