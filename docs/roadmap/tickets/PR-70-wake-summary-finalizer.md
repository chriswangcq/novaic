# PR-70 — Add wake-scope summary finalizer before archive

| Field | Value |
|---|---|
| **Ticket** | PR-70 |
| **Status** | `[✓]` |
| **Opened** | 2026-04-27 |
| **Owner** | __ |
| **Severity** | P0 memory correctness — closed wake scopes currently fold to `(no report)` and lose cross-wake meaning. |
| **Blocks** | PR-71, PR-72, PR-73 |
| **Blocked by** | PR-65 through PR-69 landed on `codex/focus-new-llm-context`. |
| **Invariant** | A closed wake scope under agent-root must have a useful `summary.md` even when the LLM only called `chat_reply`. |

## Intent

Keep the new Cortex design: agent-root remains the permanent active root, active wake scopes expand normally, and closed wake scopes fold to `summary.md`.

The missing piece is a runtime-owned finalizer that writes a concise wake report before archive. The report should represent the wake's user-visible conversation and durable facts, not blindly paste the last `chat_reply`.

## Required Behavior

- Before `subagent_rest` archives a wake scope, Runtime supplies a non-empty report when no explicit report exists.
- Explicit `skill_end(report=...)` / explicit close report still wins over generated fallback text.
- The generated wake report must be concise and future-self oriented:
  - user message(s)
  - user-visible agent reply / important tool action
  - durable facts or open threads
- The finalizer must ignore hidden retry-only assistant text and private reasoning.
- The next wake's agent-root DFS folded summaries must include the previous wake's useful report.

## Acceptance Criteria

- A normal chat turn with only `chat_reply` closes with a non-empty wake `summary.md`.
- A second wake can see the previous wake summary through agent-root DFS assembly.
- The report for a turn like `叫大哥` includes the durable fact that the user asked to be called `大哥`.
- A scope with an explicit report preserves that exact report and does not run fallback synthesis over it.
- No `<PREV_SCOPE_HISTORY>` / `<PREV_SCOPE_TAIL>` path is reintroduced.

## Engineering Checklist

### Unit Tests

- `[x]` Runtime unit test: `chat_reply`-only rest payload receives generated report.
- `[x]` Runtime/Cortex integration-style test: archived wake summary appears in the next agent-root prepared context.
- `[x]` Test explicit report precedence over generated fallback.
- `[x]` Test finalizer ignores hidden no-tool retry assistant content.

Evidence:

- `cd novaic-agent-runtime && pytest -q tests/test_pr70_wake_summary_finalizer.py tests/test_pr58_rest_summary_and_tail_render.py tests/test_pr67_wake_child_scope.py tests/test_pr65_agent_root_scope.py` → `23 passed in 0.10s`
- `cd novaic-agent-runtime && pytest -q` → `246 passed in 1.06s`
- `cd novaic-cortex && pytest -q tests/test_pr66_system_scope_rendering.py` → `4 passed in 0.03s`

### Smoke Tests

- `[x]` Local smoke: generate wake summary for `叫大哥`, close wake child, prepare agent-root context, verify folded summary contains `大哥`.
- `[x]` Production smoke: send `叫大哥`, wait for rest, inspect archived wake `summary.md`.
- `[x]` Send follow-up `谁是谁啊`; inspect actual LLM request and verify folded summary contains `大哥`.
- `[x]` Confirm the visible answer no longer forgets the requested address.

Evidence:

- Local smoke script output:
  - `SMOKE_OK`
  - folded report contained `User asked to be called 大哥`
- Production smoke:
  - User message `65637abd462b` (`叫大哥`) closed wake scope `13ca401a-3c0c-4a82-8303-20848b986b91`.
  - Agent-root prepared context included:
    - `Wake summary:`
    - `User said: 叫大哥`
    - `Agent replied: 大哥好！👋 有什么我可以帮您的？`
    - `Durable fact: User asked to be called 大哥.`
  - Follow-up user message `ad5975306cb2` (`谁是谁啊`) closed wake scope `b69d54c4-0f51-4807-9f8a-76ed90acca5e`.
  - LLM input logs `1055` and `1056` both contained `User asked to be called 大哥`.
  - Visible reply `885cdbd990e1` addressed the user as `大哥`.

### Deployment

- `[x]` Deploy Runtime and Cortex only if touched by the implementation.
- `[x]` Run health checks for Business, Queue/Runtime, Cortex.
- `[x]` Capture log/API evidence: archived `summary.md`, next LLM input excerpt, service health.

Evidence:

- `./deploy runtime` → all backends restarted successfully.
- `./deploy status` → Entangled, Gateway, Business, Device, Queue, Storage-A, Cortex healthy; Workers `8`; Relay active.
- Online Cortex prepare evidence after `13ca...` archived: folded wake summary contained `User asked to be called 大哥`.
- Online execution-log evidence for next wake: LLM logs `1055` and `1056` contained the folded `大哥` wake summary.

### GitHub / Commit

- `[x]` Commit implementation, tests, and this ticket update as one PR-sized commit.
- `[x]` Commit message should start with `runtime:` or `cortex:` and reference PR-70.
- `[x]` PR description must include unit-test output, smoke evidence, deploy evidence, and a rollback note.

Evidence:

- Runtime submodule commit: `738c885 runtime: add PR-70 wake summary finalizer`.
- Parent repo commit includes this ticket update and the runtime submodule pointer.

## Out of Scope

- User profile extraction.
- Long-term compaction policy for very large agent-root trees.
- Prompt wording cleanup beyond what is necessary for the finalizer contract.
