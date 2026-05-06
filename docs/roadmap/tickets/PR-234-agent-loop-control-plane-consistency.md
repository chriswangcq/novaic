# PR-234 — Agent Loop Control-Plane Consistency

| Field | Value |
| --- | --- |
| Status | `[x]` |
| Owner | Codex |
| Created | 2026-05-06 |
| Depends on | PR-233 active inbox / recovery design |
| Design | `docs/architecture/agent-loop-control-plane-consistency.md` |

## Goal

Make Agent loop closing behavior deterministic and recoverable by ensuring the LLM prompt, `skill_end`, stack checks, tool-result persistence, and finalization decisions all observe the same explicit control-plane state.

## Scope

- Use Cortex active-path stack as the single authoritative stack source.
- Prevent transient Active skill stack prompt snapshots from becoming durable context that can mislead later rounds.
- Treat Cortex logical failures such as `ok:false` as failed tool observations.
- Add a deterministic repeated-failure breaker for scope mismatch loops.
- Stop representing forced `round_cap` finalization as natural `stack_empty=true`.

## Large Work Orders

1. [PR-234A — Cortex authoritative stack source](PR-234A-cortex-authoritative-stack-source.md) — `[x]`
2. [PR-234B — Transient stack snapshot assembly contract](PR-234B-transient-stack-snapshot-contract.md) — `[x]`
3. [PR-234C — Runtime tool logical failure semantics](PR-234C-runtime-tool-logical-failure-semantics.md) — `[x]`
4. [PR-234D — Repeated mismatch breaker and force-finalize semantics](PR-234D-repeated-mismatch-breaker.md) — `[x]`

## Acceptance Criteria

- LLM-visible Active skill stack, `/v1/context/status`, and `/v1/context/skill_end` derive stack state from the same source.
- A `skill_end` scope mismatch is saved as an error observation, not a completed successful step.
- Repeated identical `skill_end` mismatch cannot spin until only the round cap stops it.
- `round_cap` remains a force-finalize reason and no longer lies that the stack was naturally empty.
- Tests cover each boundary with explicit inputs and no hidden runtime state.

## Verification

- `pytest` for relevant Cortex tests.
- `pytest` for relevant Runtime saga/tool tests.
- `pytest` for Common LLM assembly contract tests.
- `git diff --check` for touched tracked files.

## Deployment Checklist

- `[ ]` Code committed in each touched subrepo.
- `[ ]` Parent submodule pointers updated if needed.
- `[ ]` Runtime/Cortex deployed or explicitly deferred by user.
- `[ ]` At least two runtime evidence points captured after deploy.
