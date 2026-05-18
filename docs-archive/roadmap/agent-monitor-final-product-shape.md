# Agent Monitor Final Product Shape

| Field | Value |
| --- | --- |
| Status | Current product contract |
| Created | 2026-05-04 |
| Scope | User-facing Agent Monitor in the App |
| Source path | Runtime projects Cortex trace into Entangled `agent-activity-records` / `agent-activity-participants`; App subscribes to those entities |

## One-line Product Definition

Agent Monitor is the user's live "agent is working" channel.

It answers:

1. Is the agent handling something now?
2. What did the agent most recently observe, think, or do?
3. If I open it, can I understand this turn's working process without seeing developer diagnostics?

It is not an execution-log debugger, not message delivery status, not a task queue UI, and not a new source of truth.

## Product Surfaces

### Bottom Capsule

The bottom capsule is a compact live presence indicator.

It should show:

- Participant name, for example `Main Agent` or a subagent label.
- A status affordance:
  - running: subtle activity indicator.
  - completed/idle: quiet completed state.
  - failed: calm error state with user-readable wording.
- The latest public activity title from Entangled activity records.

It must not show:

- Hardcoded filler such as "processing message" when the actual latest activity says something else.
- Raw ids, HTTP details, MCP content, stack traces, or internal refs.
- A fake progress bar.

Clicking the capsule opens the activity layer for that participant.

### Activity Layer

The activity layer is a compact channel, not a diagnostic table.

Layout rules:

- Latest activity appears at the bottom, like a chat/game event channel.
- The layer can scroll upward to older records.
- If the user is near the bottom, new activity should keep the view pinned to the bottom.
- If the user intentionally scrolls up, new activity must not yank the scroll position.
- The header should stay minimal: participant name, current state, close button. Do not group records into heavy sections.
- The layer should stay above the composer and not overlap message bubbles incoherently.

Record row rules:

- Every row has a small status icon, a public title, and optionally a preview.
- Rows with meaningful detail are expandable inline.
- Expandable content should reveal user-safe detail, such as reasoning text, command preview, or saved turn summary.
- Non-expandable rows should stay visually light.

### Message Status

Message status is separate from Agent Monitor.

It only means user message delivery:

- Sending
- Delivered
- Failed

It must not drive agent wake loops and must not be reused as "agent read/processed" state.

## Activity Taxonomy

Agent Monitor records are public projections of the agent work trace.

| Type | User-facing meaning | Typical source |
| --- | --- | --- |
| Notification | The environment notified the agent that something is available | Environment notification |
| Observation | The agent looked at something | `im_read`, `chat_history`, `display`, `payload_read`, shell output preview |
| Reasoning | The model's thinking text | LLM provider `reasoning_content` |
| Action | The agent did something | Tool call / runtime action |
| Summary | The agent saved this turn's context | `skill_end(report=...)` |
| Failure | Something failed in the user's task path | Runtime/tool failure, redacted and translated |

### Observation

Observation rows should describe what the agent saw, not expose how storage or transport worked.

Good:

- `读取了你的消息`
- `查看了附件`
- `命令完成`
- `检索了历史对话`

Bad:

- raw tool result identifiers or payload locator strings
- Raw JSON payload.
- Raw HTTP response.
- `_mcp_content`.

### Reasoning

Reasoning comes directly from the LLM provider's `reasoning_content`.

The monitor should not invent a second reasoning summary. It may display a short preview, with the full available reasoning shown through expansion when safe.

If the provider does not produce reasoning text, no fake reasoning row is needed.

### Action

Action rows should express intent in product language.

Examples:

- `调用 shell`
- `回复你`
- `创建子 Agent`
- `读取 payload`
- `保存本轮上下文`

Implementation names may be used only when they are already meaningful to the user, for example `shell`.

### Summary

Summary rows are produced by explicit scope closure.

For the normal wake scope, the relevant summary is the `skill_end(report=...)` report. It should show as "已保存本轮上下文" with an expandable report preview.

It must not be an automatic wake summary, a chat-reply-derived memory guess, or a hidden fallback.

## Projection Rules

The App should render only public projection fields.

Preferred record shape:

- `agent_id`
- `participant_id`
- `order`
- `phase`
- `kind`
- `status`
- `public_title`
- `public_preview`
- `public_detail`
- `has_payload`
- `payload_ref`
- `created_at`

The public projection is allowed to reference payloads, but raw payloads are not part of the default monitor row.

The UI may apply presentation-level cleanup, but semantic truth should come from the projection contract, not from fragile string guessing in React.

## Detail Expansion

Expandable detail is part of the product, not a developer panel.

Allowed detail:

- LLM reasoning text.
- The content the agent explicitly observed, when it is user-safe.
- A shell/head/tail preview.
- A payload interpretation result.
- A `skill_end` report.
- A friendly failure explanation.

Forbidden detail:

- Result ids.
- Raw MCP envelope.
- Raw HTTP body.
- Stack traces.
- Secrets.
- Internal database shape.
- Transport retry metadata.

If a record has both safe public detail and debug detail, the public layer shows only safe detail. Debug detail belongs in a separate developer diagnostics surface.

## Empty, Loading, Error, Running

| State | Product behavior |
| --- | --- |
| Empty | Show a quiet empty state: "还没有活动轨迹". |
| Loading | Use a subtle loading affordance. Do not show a fake progress bar. |
| Running | Capsule shows the latest running public title; layer shows the running row. |
| Completed | Capsule shows the latest completed public title. |
| Failed | Show a friendly failure row. Hide stack traces and raw response bodies. |
| Subscription unavailable | Say activity is temporarily unavailable and will retry; diagnostics can be found elsewhere. |

## Non-goals

Agent Monitor must not become:

- A raw execution log viewer.
- A Cortex explorer.
- An Entangled inspector.
- A task queue dashboard.
- A message read/unread controller.
- A hidden memory system.
- A place where old fallback paths can leak user-visible content.

## Current Implementation Notes

As of 2026-05-04:

- Runtime materializes public activity records from trace writes.
- App reads `agent-activity-records` and `agent-activity-participants` from Entangled stream/list stores.
- The old action polling / direct Cortex projection read path has been removed.
- The current App has tests for public-surface rendering, bottom-order behavior, expansion, debug redaction, and modal/layer behavior.

Known product contract gaps to keep watching:

1. Some display text is still normalized in React from tool-ish titles. Long term, Runtime/Common should emit stronger public display fields so UI string heuristics can shrink.
2. Detail redaction is intentionally conservative. If legitimate safe content is hidden, fix the projection contract rather than adding broad UI fallbacks.
3. Bookkeeping tools should stay invisible when their observation/summary counterpart already expresses user value.
4. Subagent participant labeling should remain product-level and must not expose implementation scope ids.

## Acceptance Matrix

| Scenario | Expected monitor behavior |
| --- | --- |
| User sends a normal message | Capsule appears with the latest real activity; opening layer shows observation, reasoning/action if available, reply, and summary. |
| Agent is still thinking | Capsule shows a running state and current reasoning/action title. |
| Agent replied | Message bubble shows the reply; monitor shows the action/summary trail without duplicating raw chat status. |
| Agent saves context | Layer shows "已保存本轮上下文" with expandable report. |
| Agent uses shell | Layer shows command action plus safe output preview/ref; raw long output is not dumped. |
| Tool fails | Layer shows user-readable failure; raw stack/HTTP/MCP details stay out. |
| Large history | Latest item remains at bottom; user can scroll older records; layout does not overlap composer or bubbles. |
| Refresh / cache reload | Monitor data comes back from Entangled projection without extra HTTP action polling. |

## Follow-up Tickets

The final shape is a contract. Future implementation work should be split into small, independently mergeable tickets:

1. Strengthen Runtime public projection fields and reduce React title heuristics.
2. Add acceptance coverage for capsule latest-title freshness and running-state behavior.
3. Add acceptance coverage for bottom-pinned layer scrolling and user-scroll preservation.
4. Add acceptance coverage for reasoning/detail expansion.
5. Add guardrails that public monitor rows never include raw MCP, raw HTTP, result ids, or stack traces.
