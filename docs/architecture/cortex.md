# Cortex 认知引擎（当前架构）

> 与 **`novaic-cortex`** 代码一致；对应原 **`HANDOVER.md` §十八**。历史长文：[historical-doc-links.md](../historical-doc-links.md)；归档旧稿：`git show docs-graveyard-p2:docs/archived/`。

Cortex 为 **独立 HTTP 服务**（默认 **`19996`**，`CORTEX_PORT`），S3-backed：Workspace、**DFS Step Tree** 上下文、Recall、Sandbox。

## 存储模型

| 区域 | 管理者 | Agent 权限 | 内容 |
|------|--------|------------|------|
| `/ro/` | Cortex | 只读 | `active/`、`scopes/`、`config/`、`skills/`、`knowledge/` |
| `/rw/` | Agent | 读写 | `scratch/` |

Scope 为系统对象；创建 / 写 step / 归档用 **`_sys_*`**，绕过 `/rw/` ACL。

## Scope 树与 DFS 上下文拼装

**上下文原子单位是 step，不是 message。**

- 索引：`steps/_index.jsonl`。
- Step：**tool**（叶，JSON 文件）、**scope**（复合，`skill_begin` 子目录）。

`ContextEngine.prepare_messages_for_llm()`：

- **闭合 scope** → 折叠为一条 summary system message  
- **开放 scope** → DFS 展开子 step  
- **tool step** → assistant `tool_call` + tool result  

```
DFS(node):
  if node.type == "tool":
    yield tool_message(node)
  elif node.type == "scope":
    if node.closed:
      yield fold_message(node)
    else:
      for child in node.children:
        yield* DFS(child)
```

## context.jsonl

只放非 step 类消息（system、recall、user、assistant）。**Tool 结果**在 `steps/`，拼装时合并。

## Recall

读 `/ro/scopes/_index.jsonl`，为归档 scope 生成 system message；Agent 可用 `novaic read /ro/scopes/{sid}/...` 浏览细节。

## 核心组件（`novaic-cortex/novaic_cortex/`）

| 组件 | 文件 | 职责 |
|------|------|------|
| `Workspace` | `workspace.py` | 文件抽象与 scope/step/context CRUD |
| `WorkspaceRegistry` | `registry.py` | 多租户缓存（user_id + agent_id） |
| `ContextEngine` | `context_stack/engine.py` | DFS 拼装 |
| `StepTreeBuilder` | `context_stack/step_tree.py` | 从 S3 建内存树 |
| `budget_compact` | `context_stack/budget.py` | token 预算压缩 |
| `Recall` | `recall.py` | 归档 → system messages |
| `CortexBridge` | `novaic-agent-runtime/.../cortex_bridge.py` | Runtime 侧 HTTP 客户端 |

## Agent Runtime 集成

- Runtime 经 **`CortexBridge`（httpx）** 调 Cortex API，不直接 import Cortex。
- `skill_begin` / `skill_end` 管 scope 生命周期，**不写入**重复 tool step。
- 其它工具结果：`POST /v1/steps/write`。
- `resolve_active_scope_path`：路由到最深活跃 scope。

## 部署（生产示例）

| 项 | 值 |
|----|-----|
| 端口 | 19996 |
| S3 | `novaic-s3-bucket` / `cortex/` / `oss-cn-hongkong`（以实际配置为准） |
| 环境变量 | `ALIBABA_CLOUD_ACCESS_KEY_ID`、`ALIBABA_CLOUD_ACCESS_KEY_SECRET` |
| 启动 | `.venv/bin/python -m novaic_cortex.main_cortex` |
| 健康检查 | `GET http://localhost:19996/health` |

## 相关

- [data-ownership.md](data-ownership.md)  
- [agent-pipeline.md](agent-pipeline.md)  
