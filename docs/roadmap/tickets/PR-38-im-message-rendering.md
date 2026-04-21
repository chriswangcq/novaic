# PR-38  用户消息按 IM 语义渲染（发送方 / 时间戳 / msg_id 写入 LLM 可见 content）

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（Cortex context assembly 四连击 #3/4） |
| **Milestone** | — |
| **承诺** | 架构原则：**显式 > 隐式** + **消息是事件不是 prompt 片段** |
| **Status** | `[x]` 2026-04-22 完成 — IM header 渲染 + _metadata 结构化副本 + system prompt 说明段 + 10 unit tests |
| **Depends on** | PR-36（正序前提） |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | wangchaoqun |

## 事件摘要

用户消息从 `chat_messages` 表进入 LLM context 时被**降级成 OpenAI chat message**，丢掉了 IM 语义（发送方身份 / 时间戳 / 消息 id）。表现：

- 真人发 `USER_MESSAGE` 和兄弟 agent 发 `SUBAGENT_SEND` 在 LLM 眼里**都是 `role: user`**，无法区分；
- 3 条连发的 IM 看不出是短时间连发，还是相隔几小时；
- LLM 想引用"你刚才第二条说的…"没法精确指（没有 msg_id 可见）。

## 根因

```76:83:novaic-agent-runtime/task_queue/handlers/context_handlers.py
        for msg in filtered:
            idem_key = f"user-msg-{msg['id']}"
            ctx_msg = {
                "role": "user",
                "content": msg["content"],
                "_message_type": msg.get("type", "USER_MESSAGE"),
                "_idempotency_key": idem_key,
            }
```

- `content` 原样拷贝，**没有**发送方/时间戳/msg_id header。
- `_message_type` 只在 DB 侧留痕，LLM 看不到。
- `msg.id` 仅做幂等 key，不在 LLM 可见层。

## 修复方案

### A. Content header 加 IM 元数据

渲染函数 `_render_im_content(msg, sender_kind, sender_label)` → 返回：

```
[msg_id={id} from={sender_kind}:{sender_label} at={iso_ts}]
{原始 content}
```

- `USER_MESSAGE` → `sender_kind=user`、`sender_label=user_id`（或 `"human"` 若 user_id 为空）
- `SUBAGENT_SEND` → `sender_kind=subagent`、`sender_label=metadata.from_subagent_id`（fallback 到 `"peer"`）
- `SUBAGENT_COMPLETED` → `sender_kind=subagent_report`、`sender_label=metadata.child_subagent_id`

**ISO 时间格式**：`common.utils.time.utc_now_iso` 风格（`YYYY-MM-DDTHH:MM:SS.mmmZ`）。Msg 本身的 `timestamp` 字段（见 PR-35 双层防御后已保证非空）。

### B. `ctx_msg._metadata` 保留结构化副本

供 ContextEngine / trace 使用：

```python
ctx_msg = {
    "role": "user",
    "content": _render_im_content(msg, sender_kind, sender_label),
    "_message_type": msg.get("type", "USER_MESSAGE"),
    "_idempotency_key": idem_key,
    "_metadata": {
        "origin": "im",
        "msg_id": msg["id"],
        "sender_kind": sender_kind,
        "sender_label": sender_label,
        "timestamp": msg.get("timestamp"),
    },
}
```

### C. System prompt 补一段 IM 语义说明

`system_prompt.py` 在 agent identity 段后补：

```
## 消息阅读约定

用户侧消息（role: user）的 content 可能以 IM header 开头：
[msg_id=... from=user:USER_ID at=ISO_TIME]
<实际消息内容>

- `from=user:*` 是真人用户；`from=subagent:*` 是兄弟 agent 通过 subagent_send 发来的；
  `from=subagent_report:*` 是子 agent rest 后的汇报。
- 同一 `from` 在相近 `at` 时间戳连发的多条消息视为同一轮 IM，不必为每条单独回复。
- 回复时若需引用特定消息，可用 `msg_id=...` 精确定位（显示给用户的回复不需要带 msg_id，仅供你自己推理用）。
```

这段仅加进 system prompt —— 让 LLM 学会读 header，**不改变** OpenAI 协议里 `role` 的用法（依然全部 `user`，避免破坏 function calling 语义）。

### D. `SUBAGENT_SEND` 继续保持 `role: user`（judgment call）

考虑过用 OpenAI 的 `name` 字段区分，但：
- 部分模型（包括 GPT-4o、某些 Anthropic endpoint）对 `role: user` 的 `name` 字段支持不一致；
- 现有 fine-tune/eval 都基于 `role: user` 假设；
- Header 渲染已经足够让 LLM 区分。

所以 D：**改渲染层、不动协议层**。

### E. 回归测试

`novaic-agent-runtime/tests/test_im_rendering.py` 新增：

1. `USER_MESSAGE` 渲染 header 正确（msg_id / from=user / timestamp 都在）。
2. `SUBAGENT_SEND` 渲染 `from=subagent:*` 且带 `metadata.from_subagent_id`。
3. `SUBAGENT_COMPLETED` 渲染 `from=subagent_report:*`。
4. `metadata` 缺失 → 降级到 fallback label，不崩。
5. `timestamp` 缺失 → header 里显示 `at=unknown`，不崩（PR-35 后正常应该不缺，但防御）。
6. `_metadata.origin="im"` 和 `_metadata.msg_id` 正确写入。

## 子 PR

| # | Repo | Branch | 内容 |
|---|---|---|---|
| 1 | `novaic-agent-runtime` | `hotfix/im-message-rendering` | A + B + E（`context_handlers.py` + tests） |
| 2 | `novaic-agent-runtime` | `hotfix/system-prompt-im-section` | C（`system_prompt.py`） |
| — | 主仓 | `fix/cortex-context-assembly-36-39` | submodule bumps |

**Merge 顺序**：1 和 2 可并行，都独立不依赖。

## 验收

- 6 个新 test 全绿。
- 手动验证：
  - 2 个真人连发消息 → context.jsonl 里两条 user msg 的 content 都带 `from=user:*` header 且 `at` 递增。
  - 触发 subagent_send → context.jsonl 里出现 `from=subagent:*`。
  - LLM 回复引用 `msg_id` 能在 Business `/trace` 端点查到对应消息。

## 回滚

`git revert <commit>` —— 回到 raw content。LLM 降级为"看不到 IM header"，功能不破坏。

## 架构判定沉淀

- **协议层和渲染层分离**：OpenAI chat message schema 是协议（`role` / `content` / `name` / `tool_calls`），但 **content 内部**可以带结构化信息。把 IM 元数据渲染进 content 是**渲染层**行为，不污染协议。
- **Metadata 分两段**：LLM 可见（写进 content header）+ LLM 不可见（写进 `_metadata`，供 trace / context engine 消费）。不要用 `_metadata` 替代 header —— LLM 看不见的字段等于不存在。
