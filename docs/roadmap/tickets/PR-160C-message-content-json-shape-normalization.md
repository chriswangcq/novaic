# PR-160C — Message Content JSON Shape Normalization

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-160 |
| Repos | novaic-agent-runtime, novaic-business, novaic-app, online data, docs |

## Goal

把 `chat_messages.content` 收口为单一 JSON shape：`{"text": "...", "attachments": [...]}`。不再让 Agent reply 写 raw string，也不再让客户端把 raw string 当作可显示消息兼容。

## Current-State Analysis

线上 `/opt/novaic/data/entangled.db` 证据：

- `chat_messages.content` 有 32 行 `json_valid(content)=0`。
- 样本全部是 `AGENT_REPLY` raw string；`USER_MESSAGE` 已经是 JSON text + attachments shape。

活代码状态：

- Runtime `chat_reply` executor 仍写 `content: message` raw string。
- Business user-message / agent-chat-event 路径已经对主路径写 JSON content，但 `agent_chat_event` 的非 `AGENT_REPLY` 分支仍可能写 raw string。
- App `parseMessageContent` 在 JSON parse 失败时直接把 raw string 当正文显示，这是旧 shape fallback。

## Implementation Plan

- [x] Runtime：`chat_reply` 写 `content={"text": message, "attachments": normalized_attachments}`。
- [x] Business：`agent_chat_event` 所有消息类型都写标准 JSON content shape。
- [x] App：移除 raw string display fallback；invalid message content fail-closed，不再显示旧 shape。
- [x] Online data：把已有 invalid raw string content 迁移为 JSON object。
- [x] 单元测试：覆盖 Runtime writer、Business event writer、App parser。
- [x] 部署 runtime/business/app 相关后端，并验证线上 invalid content count 为 0。
- [x] Git 提交。

## Done Criteria

- [x] Runtime writer test expects JSON content object.
- [x] Business test covers non-`AGENT_REPLY` event still emits JSON content.
- [x] App parser test proves raw string no longer renders as message text.
- [x] Online `chat_messages` has zero invalid JSON content rows.
- [x] Backend services healthy after deploy.
- [x] Git commits recorded.

## Verification

- `cd novaic-agent-runtime && python3 -m pytest tests/unit/task_queue/test_tool_handlers_chat_reply.py tests/unit/task_queue/test_tool_handlers_display_chat_history.py` → 12 passed.
- `cd novaic-business && python3 -m pytest tests/test_pr160_message_content_shape.py tests/test_schema_invariants.py` → 6 passed.
- `cd novaic-app && npm run test:unit -- src/application/converters.test.ts src/components/Visual/executionLogUtils.test.ts` → 11 passed.
- `./deploy runtime`, `./deploy business`, `./deploy frontend` → deployed.
- Online migration result: `invalid_content = 0`, `agent_reply_json_rows = 32`.
- `./deploy status` → all backend services healthy; relay active.
