# PR-37  修复 No-Tool Warning 失效（显式信号通道 + 去掉 `messages[-1]` 启发式）

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（Cortex context assembly 四连击 #2/4） |
| **Milestone** | — |
| **承诺** | 架构原则：**无静默失败** + **显式 > 隐式** |
| **Status** | `[x]` 2026-04-22 完成 — saga 透传 no_tool_retry_count + handler 用显式信号 + 6 unit tests |
| **Depends on** | — |
| **Blocks** | — |
| **估时** | 0.25 d |
| **Owner** | wangchaoqun |

## 事件摘要

LLM 返回纯文本（无 `tool_calls`），**应该**被 `NO_TOOL_WARNING` system 提示纠正；当前代码里 warning 文案仍在，但注入条件被两处因素污染，**skill 活跃时 100% 不发**，其他场景也不稳定。

## 根因（铁证）

**问题 A：`Step 4a` 先 append skill stack system → 污染 `Step 4b` 的 `messages[-1]` 判定**

```330:341:novaic-agent-runtime/task_queue/handlers/cortex_handlers.py
    # Step 4a: inject active skill stack snapshot so the LLM knows which
    # scope_id to pass to skill_end.
    stack_msg = _format_skill_stack_system_message(stack)
    if stack_msg:
        messages.append({"role": "system", "content": stack_msg})

    # Step 4b: transient NO_TOOL_WARNING
    if (messages
            and messages[-1].get("role") == "assistant"
            and not messages[-1].get("tool_calls")):
        logger.info("[cortex.prepare_llm_context] Injecting NO_TOOL_WARNING (transient)")
        messages.append({"role": "system", "content": NO_TOOL_WARNING})
```

一旦 skill stack 非空（`skill_begin` 后、`skill_end` 前的所有轮次），`messages[-1]` 变成 `role: "system"`，4b 条件永远为 False。

**问题 B：Saga 已经有 `no_tool_retry_count` 状态，却没传进 cortex handler**

```45:51:novaic-agent-runtime/task_queue/sagas/react_think.py
def _build_prepare_context_payload(ctx):
    return {
        "scope_id": ctx["scope_id"],
        "agent_id": ctx.get("agent_id", ""),
        "subagent_id": ctx.get("subagent_id", ""),
        "user_id": ctx.get("user_id", ""),
    }
```

Saga 在 `ctx` 里有 `no_tool_retry_count`（`react_think.py:171-172` 透传到下一轮）。Handler 本来可以基于这个确定信号注入 warning，却只能靠"看 `messages[-1]` 是不是 assistant 空回复"猜——这是**两套冗余状态**（saga 有显式计数 + handler 做启发式推断），还刚好会互相打架。

**问题 C：`budget_compact` 可能重排/压缩 `messages`**

`ContextEngine.prepare_messages_for_llm` 末尾跑 `budget_compact`，如果触发 warm/emergency 路径，消息列表可能被裁剪，`messages[-1]` 语义失守。

## 修复方案

### A. Saga 显式传信号（**根因 B**）

`_build_prepare_context_payload` 透传 `no_tool_retry_count`：

```python
def _build_prepare_context_payload(ctx):
    return {
        "scope_id": ctx["scope_id"],
        "agent_id": ctx.get("agent_id", ""),
        "subagent_id": ctx.get("subagent_id", ""),
        "user_id": ctx.get("user_id", ""),
        "no_tool_retry_count": ctx.get("no_tool_retry_count", 0),
    }
```

### B. Handler 用显式信号取代 `messages[-1]` 启发式（**根因 A + C**）

`handle_cortex_prepare_llm_context` Step 4b 改为：

```python
# Step 4b: transient NO_TOOL_WARNING — triggered by explicit saga signal,
# not by fragile `messages[-1]` inspection (which Step 4a's skill-stack
# append breaks, and which budget_compact can reorder).
if payload.get("no_tool_retry_count", 0) > 0:
    logger.info(
        "[cortex.prepare_llm_context] Injecting NO_TOOL_WARNING "
        "(no_tool_retry=%d)", payload.get("no_tool_retry_count"),
    )
    messages.append({"role": "system", "content": NO_TOOL_WARNING})
```

**注入顺序不变**：4a skill stack → 4b warning（LLM 看到 stack 提示在前、warning 在后，warning 为最后可见 hint 最醒目）。

### C. 观测

- 删除当前隐式判定 → 新增日志：`event=no_tool_warning_injected scope=<id> round=<n> retry=<k>`。
- Metric（PR-32 体系）：新增 counter `no_tool_warning_injected_total{agent_id}`（防回归 —— 如果某环境一段时间该指标为 0 说明 LLM 正常调工具；某环境长时间 >0 说明 LLM 病得不轻）。

### D. 回归测试

`novaic-agent-runtime/tests/test_no_tool_warning.py` 新增 4 个用例：

1. `no_tool_retry_count=0` + 无 skill stack + `messages[-1]=assistant(empty)` → **不注入**（防止 false positive —— 首轮空回复应该由 saga 决策层重试而不是 warning，warning 只在重试轮注入）。
2. `no_tool_retry_count=1` + 无 skill stack → 注入 warning。
3. `no_tool_retry_count=1` + **skill stack 非空**（messages[-1]=system stack msg）→ **仍然注入**（这是修复点）。
4. `no_tool_retry_count=0` → 不注入（baseline）。

## 子 PR

| # | Repo | Branch | 内容 |
|---|---|---|---|
| 1 | `novaic-agent-runtime` | `hotfix/no-tool-warning-explicit-signal` | A + B + D（saga + handler + tests） |
| — | 主仓 | `fix/cortex-context-assembly-36-39` | submodule bumps |

## 验收

- 4 个新 test 全绿。
- 手动验证：造一个 skill stack 非空（进入 skill）且 LLM 返回空文本 → 日志出现 `event=no_tool_warning_injected`，LLM 下一轮能正确 `skill_end` 或调工具。
- 之前静默失败的 session（skill 内无限空回复）不再出现。

## 回滚

`git revert <commit>` —— 回到启发式（现状：warning 部分失效但不会 crash）。

## 架构判定沉淀

- **saga 状态 vs handler 推断 —— 单一真相源**：凡是 saga 已经追踪的决策状态（retry_count、round_num、stack_hold_retry_count 等），handler 层不再独立推断，一律从 payload 读。Handler 只负责基于 payload 的**确定性**行为。
- **"看 `messages[-1]`" 是反模式**：context 经过 `budget_compact` / skill stack 注入等后处理后，尾部语义不稳定。未来任何"看最后一条消息"的判定都应该过 review，改成显式信号。
