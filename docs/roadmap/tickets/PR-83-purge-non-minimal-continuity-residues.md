# PR-83 — Purge non-minimal continuity residues from active paths

| Field | Value |
|---|---|
| **Ticket** | PR-83 |
| **Status** | `[code]` |
| **Opened** | 2026-04-28 |
| **Owner** | __ |
| **Severity** | P0 architecture cleanup — multiple old continuity concepts make the active model harder to reason about. |
| **Depends on** | PR-78; may absorb or supersede PR-79 / PR-81 if those have not landed. |
| **Blocks** | PR-84 / PR-85 guardrails are cleaner after active residue is removed. |
| **Invariant** | The only normal durable summary path is `skill_end(report=...) -> summary.md`. Runtime cleanup does not create memory. |

## Background

The chosen continuity model is intentionally small:

```text
active scope expanded
closed scope folded by summary.md
summary.md written from skill_end(report=...)
context assembled by Cortex DFS
```

The active backend should not contain alternative continuity concepts:

- wake summary
- automatic summary
- summary inferred from `chat_reply`
- Recall snippets in LLM context
- meta skill / meta scope as an LLM-facing concept
- `subagent_rest` as an LLM-facing end-of-turn concept
- `historical_summary` / `handoff_notes` as active memory fields

## Goal

Remove or clearly retire active-path wording and code that implies another summary or memory path.

This ticket is not allowed to make summaries more structured. It only removes misleading structure.

## Non-Goals

- Do not add user profile.
- Do not add automatic fact extraction.
- Do not add a summary schema.
- Do not make Cortex decide what facts matter.
- Do not remove IM replay itself; just keep it named as message delivery, not memory.

## Implementation Checklist

### 1. Active prompt and tool wording

- [x] Remove "wake summary" wording from active system prompt construction.
- [x] Remove "meta skill" / "meta scope" instructions from active tool descriptions.
- [x] Ensure `skill_end` description says it closes the current stack-top scope and persists `report` as that scope's `summary.md`.
- [x] Ensure simple chat turns do not instruct the LLM to invent memory through another mechanism.

### 2. Runtime continuity cleanup

- [x] Remove any code-side generation of durable summaries from chat text.
- [x] Ensure `wake_finalize` remains structural lifecycle cleanup, not summary writing.
- [x] Ensure force-finalize does not write fake `summary.md`.
- [x] Rename or remove remaining `subagent_rest` lifecycle concepts if they are now wake-finalize concepts.

### 3. Legacy field cleanup

- [x] Confirm `historical_summary` and `handoff_notes` have no live read/write path.
- [x] Delete them from authoritative schema if data reset is acceptable.
- [x] Otherwise add a removal deadline and active-path grep guard.

### 4. Recall cleanup

- [x] Confirm no active LLM context assembly path calls Cortex Recall.
- [x] Confirm `/recall` docs are retired/history only.
- [x] Add grep guard for active code if needed.

### 5. IM replay wording

- [ ] Keep IM replay documented as message delivery reliability.
- [ ] Do not describe IM replay as memory or cognitive continuity.

## Unit Test Requirements

- [x] Prompt contract test: generated active system prompt contains no `Wake summary`, `meta skill`, or `subagent_rest` end-turn instruction.
- [x] Runtime test: `wake_finalize` with empty report does not create or overwrite `summary.md`.
- [x] Continuity test: only `skill_end(report)` writes the folded summary.
- [x] Legacy field test: active schema or active APIs do not expose `historical_summary` / `handoff_notes`, unless explicitly quarantined.

## Smoke Test Requirements

- [ ] Trigger a simple wake.
- [ ] Inspect LLM request snapshot:
  - [ ] no `Wake summary`
  - [ ] no meta skill instruction
  - [ ] no Recall block
  - [ ] current active scope stack is present
  - [ ] prior closed scopes render through folded summaries only
- [ ] Force-finalize a test wake and verify no fake user-memory summary appears next wake.

## Deployment Checklist

- [ ] Merge code in affected subrepos.
- [ ] Update parent repo submodule pointers if subrepos changed.
- [ ] Deploy affected services:
  - [ ] runtime
  - [ ] cortex if context assembly/tool descriptions changed there
  - [ ] business if prompt construction or schemas changed there
- [ ] Capture production evidence:
  - [ ] one LLM request snapshot grep showing no old continuity residue.
  - [ ] one normal folded summary coming from `skill_end(report)`.

## GitHub / Commit Checklist

- [ ] Commit subrepo changes in each affected submodule.
- [ ] Commit parent docs/submodule pointer changes.
- [ ] PR description links this ticket and any superseded PR-79/80/81 work.
- [ ] PR description includes grep results for retired words.
- [ ] PR description includes smoke request snapshot evidence.
- [ ] PR description includes deployment evidence before marking `[x]`.

## Acceptance Criteria

- Active prompt/tool/context paths describe one summary mechanism: `skill_end(report=...)`.
- Runtime cleanup is visibly separate from cognitive continuity.
- No active code path derives durable memory from `chat_reply`.
- No active LLM context path injects Recall, wake summary, or legacy continuity fields.

## Rollback

Rollback if the LLM can no longer close the current wake scope or if folded summaries disappear from subsequent context. This ticket should not change the semantic content of summaries, only remove competing paths.
