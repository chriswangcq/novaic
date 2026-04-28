# PR-85 — Add LLM context smoke guardrails for the minimal structure path

| Field | Value |
|---|---|
| **Ticket** | PR-85 |
| **Status** | `[code]` |
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
- [ ] Child subagent turn where `subagent_report` exposure is role-appropriate.
- [ ] No-tool retry / force-finalize path.

### 3. Structural assertions

- [x] System prompt comes before scope tree context.
- [x] Closed scopes appear folded through `summary.md`.
- [x] Active scope is expanded.
- [x] Active scope stack appears and references the actual current stack top.
- [x] `tools[]` contains the tools referenced by quick-reference text.
- [x] No active request contains `Wake summary`, Recall injection, meta skill close instruction, or Tools Server/MCP wording.

### 4. Tool result id hygiene

- [x] Ensure tool result messages use the actual tool call id / traced result id expected by the provider.
- [x] Preserve `reasoning_content` if the provider/debug path needs it.
- [x] Avoid replacing tool result content with unrelated MCP payloads.

## Unit Test Requirements

- [ ] Snapshot test for each required scenario.
- [x] Contract test comparing prompt quick-reference tool names against actual `tools[]`.
- [x] Contract test for message order.
- [x] Contract test for tool call result id matching.

## Smoke Test Requirements

- [ ] Run a local or staging chat wake and save sanitized request snapshot.
- [ ] Verify a second wake sees prior folded summary.
- [ ] Verify a simple reply turn calls `chat_reply` and then closes the current wake with `skill_end`.
- [ ] Verify no old continuity terms appear in the snapshot.

## Deployment Checklist

- [ ] Merge harness/tests.
- [ ] Deploy only if Runtime/Cortex request-building code changed.
- [ ] Capture production or staging evidence:
  - [ ] one sanitized LLM request snapshot;
  - [ ] one successful smoke conversation transcript;
  - [ ] grep output proving old terms absent from the request.

## GitHub / Commit Checklist

- [ ] Commit subrepo changes.
- [ ] Commit parent submodule pointer updates and docs.
- [ ] PR description links this ticket.
- [ ] PR description includes snapshot diff or structural assertion output.
- [ ] PR description includes smoke evidence.
- [ ] PR description includes deployment evidence if runtime code changed.

## Acceptance Criteria

- A future prompt/tool/context regression shows up as a snapshot or contract-test failure.
- Actual LLM calls are inspectable without dumping sensitive full prompts.
- The smoke path demonstrates the minimal structure:
  - scope tree continuity,
  - LLM-written summaries,
  - no automatic memory path.

## Rollback

Rollback only the harness if it creates noisy or flaky tests. Do not rollback the underlying minimal-structure contract without explicit architecture review.
