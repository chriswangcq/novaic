# PR-85 — Add LLM context smoke guardrails for the minimal structure path

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| Field | Value |
|---|---|
| **Ticket** | PR-85 |
| **Status** | `[x]` closed — Runtime request-contract guardrails landed |
| **Opened** | 2026-04-28 |
| **Owner** | __ |
| **Severity** | P0 regression prevention — after old paths are removed, real LLM requests must be easy to inspect and compare. |
| **Depends on** | PR-82, PR-83, PR-84 preferred. |
| **Blocks** | Safe future cleanup of Business/Runtime boundaries. |
| **Invariant** | Representative LLM calls should show the minimal Cortex structure and no competing continuity path. |

## Background

Unit tests protect Cortex mechanics, but recent issues were discovered by looking at actual LLM request payloads:

- prompt/context ordering drift;
- old summary wording still visible;
- tool results with confusing content;
- raw assistant text not delivered through `chat_reply`;
- scope history missing or folded incorrectly.

This ticket adds smoke-level guardrails around real or near-real LLM request snapshots.

## Goal

Create repeatable smoke checks for the actual LLM context contract:

```text
system prompt
folded closed scopes from agent-root DFS
current wake active context
active scope stack
tools[] matching tool descriptions
```

## Closure — 2026-05-01

This ticket is closed. `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py` covers the sanitized request contract: prompt/context order, active stack rendering, tool schema alignment, banned old continuity terms, tool-result id preservation, and reasoning-content preservation for diagnostics.

## Non-Goals

- Do not judge LLM summary content quality.
- Do not require a fixed summary template.
- Do not snapshot secrets, full prompts with private content, or large production data.
- Do not make smoke tests depend on a specific external model response when a local fake model can verify structure.

## Implementation Checklist

### 1. Snapshot harness

- [x] Add a small harness that captures sanitized LLM request payloads for representative turns.
- [x] Redact API keys, user secrets, and long content.
- [x] Preserve message role/order, tool names, tool call ids, and scope block markers.
- [x] Store golden snapshots or structural assertions in tests.

### 2. Required scenarios

- [x] First simple chat wake.
- [x] Preference/fact turn where LLM chooses its own `skill_end(report)`.
- [x] Next wake after a folded summary exists.
- [x] Shell-enabled debugging turn.
- [x] Child subagent turn where `subagent_report` exposure is role-appropriate. Superseded by PR-123..PR-129: subagent communication now uses IM, and `subagent_report` is no longer an LLM tool path.
- [x] No-tool retry / force-finalize path. Covered by PR-71 no-tool retry cleanup and Runtime finalize-summary-boundary tests.

### 3. Structural assertions

- [x] System prompt comes before scope tree context.
- [x] Closed scopes appear folded through `summary.md`.
- [x] Active scope is expanded.
- [x] Active scope stack appears and references the actual current stack top.
- [x] `tools[]` contains the tools referenced by quick-reference text.
- [x] No active request contains `Wake summary`, Recall injection, or meta skill close instruction.

### 4. Tool result id hygiene

- [x] Ensure tool result messages use the actual tool call id / traced result id expected by the provider.
- [x] Preserve `reasoning_content` if the provider/debug path needs it.
- [x] Avoid replacing tool result content with unrelated MCP payloads.

## Unit Test Requirements

- [x] Structural snapshot/contract coverage for each current required scenario; retired scenarios are covered by deletion guardrails rather than golden snapshots.
- [x] Contract test comparing prompt quick-reference tool names against actual `tools[]`.
- [x] Contract test for message order.
- [x] Contract test for tool call result id matching.

## Smoke Test Requirements

- [x] Run a local or staging chat wake and save sanitized request snapshot.
- [x] Verify a second wake sees prior folded summary.
- [x] Verify a simple reply turn calls `chat_reply` and then closes the current wake with `skill_end`.
- [x] Verify no old continuity terms appear in the snapshot.

## Deployment Checklist

- [x] Merge harness/tests.
- [x] Deploy only if Runtime/Cortex request-building code changed.
- [x] Capture production or staging evidence:
  - [x] one sanitized LLM request snapshot;
  - [x] one successful smoke conversation transcript;
  - [x] grep output proving old terms absent from the request.

## GitHub / Commit Checklist

- [x] Commit subrepo changes.
- [x] Commit parent submodule pointer updates and docs.
- [x] PR description links this ticket.
- [x] PR description includes snapshot diff or structural assertion output.
- [x] PR description includes smoke evidence.
- [x] PR description includes deployment evidence if runtime code changed.

## Acceptance Criteria

- A future prompt/tool/context regression shows up as a snapshot or contract-test failure.
- Actual LLM calls are inspectable without dumping sensitive full prompts.
- The smoke path demonstrates the minimal structure:
  - scope tree continuity,
  - LLM-written summaries,
  - no automatic memory path.

## Rollback

Rollback only the harness if it creates noisy or flaky tests. Do not rollback the underlying minimal-structure contract without explicit architecture review.
