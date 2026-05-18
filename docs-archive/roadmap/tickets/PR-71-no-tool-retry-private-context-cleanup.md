# PR-71 — Keep no-tool retry attempts out of canonical LLM context

| Field | Value |
|---|---|
| **Ticket** | PR-71 |
| **Status** | `[✓]` |
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

- `[x]` Runtime test: no-tool first response is not appended to Cortex context.
- `[x]` Runtime test: tool-call response is still appended.
- `[x]` Context sanitization test: `reasoning_content` is stripped from LLM-bound messages.
- `[x]` Retry test: transient warning behavior still passes existing PR-37 coverage.

Evidence:

- `cd novaic-agent-runtime && pytest -q tests/test_pr71_no_tool_retry_context_cleanup.py tests/test_no_tool_warning.py` → `11 passed in 0.07s`
- `cd novaic-agent-runtime && pytest -q` → `251 passed in 0.95s`

### Smoke Tests

- `[x]` Simulate a no-tool first LLM response in unit coverage.
- `[x]` Inspect execution logs: raw response remains available diagnostically.
- `[x]` Inspect production LLM input: `reasoning_content` is absent.

Evidence:

- Production smoke user message `a3b7b943b1a2` (`嗯`) closed scope `e5a06ce0-879b-42b3-900b-e94600ea84e1`.
- Visible reply `0e7515a5a3af` addressed the user as `大哥`, proving normal `chat_reply` still works after the save-response condition change.
- Execution log `1058` input: `input_has_reasoning_content=False`, `input_has_dage=True`.
- Execution log `1059` tool input/result: no `reasoning_content`.

### Deployment

- `[x]` Deploy Runtime.
- `[x]` Run health checks and one normal chat smoke after deploy.
- `[x]` Capture LLM call excerpt showing clean context.

Evidence:

- `./deploy runtime` → all backends restarted successfully.
- `./deploy status` → Entangled, Gateway, Business, Device, Queue, Blob Service, Cortex healthy; Workers `8`; Relay active.

### GitHub / Commit

- `[x]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[x]` Commit message should reference PR-71.
- `[x]` PR description must include before/after LLM input evidence and rollback note.

Evidence:

- Runtime submodule commit: `9dd2fee runtime: keep no-tool retries out of context`.
- Parent repo commit includes this ticket update and the runtime submodule pointer.

## Out of Scope

- Changing summary generation policy beyond ignoring hidden retry text.
- Changing execution-log retention.
