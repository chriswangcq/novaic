# PR-71 — Keep no-tool retry attempts out of canonical LLM context

| Field | Value |
|---|---|
| **Ticket** | PR-71 |
| **Status** | `[ ]` |
| **Opened** | 2026-04-27 |
| **Owner** | __ |
| **Severity** | P0 context correctness — invisible assistant text and reasoning currently leak into retry context. |
| **Blocks** | PR-72, PR-73 |
| **Blocked by** | PR-70 preferred, but can be implemented independently. |
| **Invariant** | If the user cannot see a plain assistant reply because no tool was called, that hidden reply must not become canonical conversational memory. |

## Intent

No-tool retry should be a control-flow repair, not a source of ghost assistant messages.

When the LLM returns plain text without tools, the user does not see it. Persisting that plain text into Cortex makes the next retry think it already answered and pollutes future summaries.

## Required Behavior

- Plain assistant responses with no tool calls in a no-tool retry path must not be appended to canonical wake context.
- Tool-call assistant messages are still persisted so tool results can attach correctly.
- LLM `reasoning_content` must not be rendered into future LLM calls.
- Retry warning remains transient and does not become archived conversation.
- Execution logs can still retain raw LLM responses for diagnostics.

## Acceptance Criteria

- A first no-tool response triggers retry without adding visible assistant `content` to the next LLM `messages`.
- A retry LLM input contains the user message and transient warning, not the previous hidden assistant answer.
- `reasoning_content` is absent from normal prepared LLM context.
- Tool-call responses still appear with `tool_calls` and can be executed.

## Engineering Checklist

### Unit Tests

- `[ ]` Runtime test: no-tool first response is not appended to Cortex context.
- `[ ]` Runtime test: tool-call response is still appended.
- `[ ]` Context sanitization test: `reasoning_content` is stripped from LLM-bound messages.
- `[ ]` Retry test: transient warning appears once and is not persisted.

### Smoke Tests

- `[ ]` Force or simulate a no-tool first LLM response.
- `[ ]` Inspect execution logs: raw response is available diagnostically.
- `[ ]` Inspect second LLM input: hidden assistant content and `reasoning_content` are absent.

### Deployment

- `[ ]` Deploy Runtime.
- `[ ]` Run health checks and one normal chat smoke after deploy.
- `[ ]` Capture LLM call excerpt showing clean retry context.

### GitHub / Commit

- `[ ]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[ ]` Commit message should reference PR-71.
- `[ ]` PR description must include before/after LLM input evidence and rollback note.

## Out of Scope

- Changing summary generation policy beyond ignoring hidden retry text.
- Changing execution-log retention.
