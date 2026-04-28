# 统一时间线与 DFS 上下文拼装

> 源码：`novaic_cortex/context_stack/engine.py`、`context_stack/step_tree.py`、`context_stack/budget.py`。

当前 LLM context 主路径是：

1. 读取当前入口 scope 的 `context.jsonl`。
2. 从 `steps/_index.jsonl` 构建 Step Tree。
3. 合并普通消息、assistant message、tool result 与 scope fold。
4. 对整条 messages 调 `budget_compact`。

入口通常是 **agent-root scope**，因此历史 wake scope 会作为 agent-root 下的 child scope 被 DFS 处理。

## 1. 数据源

| 数据 | 用途 |
|------|------|
| `context.jsonl` | 少量非 step 类消息。当前系统提示由 Runtime prompt builder 注入，不靠 `meta.recall_messages`。 |
| `steps/_index.jsonl` | 按 seq 递增的 step 时间线。 |
| `steps/*.json` | assistant/tool/env 等 step payload。 |
| `steps/{NNNN_scope_<id>}/` | 子 scope 目录。 |
| `summary.md` | scope 被 `skill_end(report=...)` 关闭时写入；闭合后用于 fold。 |

`meta.json` 仍记录 scope 生命周期字段，但当前主路径不从 `meta.json` 注入独立 Recall 或 wake-summary 通道。

## 2. Step 类型

| `type` | 含义 | LLM 渲染 |
|--------|------|----------|
| `env` | 环境/输入事件 | system 或 user 相关上下文，由具体 payload 决定 |
| `assistant` | LLM assistant message | assistant，保留 `content`、`tool_calls`、`reasoning_content` |
| `tool` | 工具执行结果 | tool message，`tool_call_id` + 结果内容 |
| `scope` | 子 scope 目录 | 开放则 DFS 展开，已关闭则按 `summary.md` 折叠 |

## 3. Scope DFS 规则

```text
agent-root
  wake-1 (closed, summary.md)      -> fold
  wake-2 (closed, summary.md)      -> fold
  wake-3 (open)
    child-skill (closed, summary)  -> fold inside wake-3
    current steps                  -> expand
```

折叠输出由 `render_scope_fold` 生成，形如：

```text
[Skill '<scope name>' completed]
<summary.md>
```

空 `summary.md` 会被抑制，避免结构性 cleanup 产生假记忆。

## 4. Active Stack

`ContextEngine.status(messages)` 基于 Step Tree 提取仍开放的 scope frames。Runtime 会把它追加为瞬态 system message：

```text
[Active scope stack (LIFO — close innermost first)]
  depth 0: user conversation (scope_id=<wake>)
→ Stack top: scope_id=<wake> ...
```

这条提示不写入 `context.jsonl`，每次 LLM 调用前重新生成。LLM 应按栈顶调用 `skill_end(report=...)`。

## 5. Budget Compact

`prepare_messages_for_llm` 最后调用 `budget_compact(messages, config, counter=...)`。配置来自 `EngineConfig` → `CompactConfig` 映射；详见 [budget-compact-algorithm.md](budget-compact-algorithm.md)。

## 相关文档

- [step-index-and-payload-schema.md](step-index-and-payload-schema.md)
- [session-meta-json.md](session-meta-json.md)
- [budget-compact-algorithm.md](budget-compact-algorithm.md)
- [agent-runtime-cortex-call-chain.md](agent-runtime-cortex-call-chain.md)
- [scope-lifecycle.md](scope-lifecycle.md)
- [recall.md](recall.md)（历史/已退役）
