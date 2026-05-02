# Cortex 认知引擎（当前架构）

> 详细总览：[../cortex-architecture.md](../cortex-architecture.md)。专题拆页：[../cortex/README.md](../cortex/README.md)。本节是父仓 L2 纲要。

Cortex 是独立 HTTP 服务（默认 **19996**），主职责只有两类：

1. 维护 **LIFO scope 树**。
2. 从 scope 树按 DFS 拼装 **LLM context**。

它还提供 Workspace、Sandbox 与能力 JWT。当前主路径**没有独立 Recall 模块、wake summary、自动总结、业务代理或从 `im_reply` / 聊天文本推断记忆**。

## 存储模型

| 区域 | 管理者 | Agent 权限 | 内容 |
|------|--------|------------|------|
| `/ro/` | Cortex | 只读 | `active/`、`scopes/`、`config/`、`skills/`、`knowledge/` |
| `/rw/` | Agent | 读写 | `scratch/` |

Scope 是系统对象；创建、写 step、归档走 `_sys_*` 内部路径，绕过 `/rw/` ACL。

## Scope 树与 DFS 上下文

上下文原子单位是 **step**，不是普通 message。

- 索引：`steps/_index.jsonl`
- Step 类型：`assistant`、`tool`、`env`、`scope`
- `scope` step 是子目录：开放时 DFS 展开，关闭且有非空 `summary.md` 时折叠成 system message

```text
DFS(node):
  if node.type == "tool":
    yield tool_call_result(node)
  elif node.type == "assistant":
    yield assistant_message(node)
  elif node.type == "scope":
    if node.closed:
      yield fold_message_from_summary_md(node)
    else:
      for child in node.children:
        yield* DFS(child)
```

## Agent Root / Wake Scope

Agent Runtime 在 `session_init` 时确保一个长期存在的 `agent_root` scope，然后在其下创建本轮 `wake` scope：

- `context.prepare_for_llm` 从 `agent_root` 开始渲染，所以历史 wake 会自然以折叠 scope 的形式出现。
- LLM 可见的 Active scope stack 隐藏 agent root，只显示当前 wake scope 与 wake 内子 skill。
- 本轮完成时，LLM 应调用 `skill_end(report=...)` 关闭当前 wake scope；该 report 原样成为 wake scope 的 `summary.md`。
- `wake_finalize` 只做结构性清理，不生成、拼接或猜测摘要。

需要额外折叠的复杂子任务，可以在 wake 内再 `skill_begin` 子 skill，并用 `skill_end(report=...)` 关闭。

## context.jsonl

`context.jsonl` 只保留少量非 step 类消息。当前 LLM 主上下文以 Step Tree / DFS 渲染为准；工具结果、assistant message、scope 折叠都从 `steps/` 与子 scope 目录拼装。

## 核心组件（`novaic-cortex/novaic_cortex/`）

| 组件 | 文件 | 职责 |
|------|------|------|
| `Workspace` | `workspace.py` | `/ro`/`/rw` ACL、scope 创建/结束/归档、step/context CRUD |
| `WorkspaceRegistry` | `registry.py` | 按 user 缓存 `S3Store`，按 `(user_id, agent_id)` 缓存 `Workspace` |
| `ContextEngine` | `context_stack/engine.py` | LLM messages 拼装入口 |
| `StepTreeBuilder` | `context_stack/step_tree.py` | 从 `_index.jsonl` 建树、折叠已关闭 scope |
| `budget_compact` | `context_stack/budget.py` | token 预算压缩 |
| `Sandbox` | `sandbox.py` | 物化 workspace → shell → 回写 `/rw` |
| `CortexBridge` | `novaic-agent-runtime/.../cortex_bridge.py` | Runtime 侧 HTTP 客户端 |

## Agent Runtime 集成

- Runtime 经 `CortexBridge` 调 Cortex API，不直接 import Cortex。
- `skill_begin` / `skill_end` 管 LLM 可见 scope 生命周期。
- `/v1/scope/end` 是结构性 API：非空 `report` 会被拒绝。
- 其它工具结果通过 `/v1/steps/write` 写入当前 active scope。
- `resolve_active_scope_path` 路由到最深活跃 scope，保证工具写在当前 wake/skill 内。

## 部署（生产示例）

| 项 | 值 |
|----|----|
| 端口 | 19996 |
| S3 | `novaic-s3-bucket` / `cortex/` / `oss-cn-hongkong`（以实际配置为准） |
| 环境变量 | `ALIBABA_CLOUD_ACCESS_KEY_ID`、`ALIBABA_CLOUD_ACCESS_KEY_SECRET` |
| 启动 | `.venv/bin/python -m novaic_cortex.main_cortex` |
| 健康检查 | `GET http://localhost:19996/health` |

## 相关

- [agent-pipeline.md](agent-pipeline.md)
- [../cortex/scope-lifecycle.md](../cortex/scope-lifecycle.md)
- [../cortex/context-timeline-and-dfs.md](../cortex/context-timeline-and-dfs.md)
