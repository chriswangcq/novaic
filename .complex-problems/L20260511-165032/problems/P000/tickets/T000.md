# Split audit by integration boundary

## Problem Definition

The repository has gone through multiple infrastructure cutovers: FSM/session/outbox, shell capability migration, LogicalFS/Sandbox service split, and event-sourced Cortex context. A previous production stall showed a subtle adapter miss: the new LogicalFS substrate existed, but a Cortex shell entrypoint still used broad legacy materialization. We need find similar misses across integration boundaries.

## Proposed Solution

Split the audit into focused child problems by boundary:

- Cortex/LogicalFS/Sandbox materialization and filesystem semantics.
- Agent Runtime Queue/FSM/Saga/session/outbox dispatch and worker wiring.
- Shell capability/tool CLI exposure and harness boundary migration.
- Cortex context event source/read-path/write-path and remaining DFS/legacy projection usage.
- Deployment/process wiring and compatibility residue that could keep old logic live.

Each child problem should run targeted source searches, inspect relevant code slices, classify findings as live-path gap vs residue, and record evidence.

## Acceptance Criteria

- Child problems exist for each major integration boundary.
- Each child result names confirmed gaps, non-issues, and uncertain follow-ups with file/function evidence.
- The final parent result consolidates findings by priority and names which issues should be fixed first.
- The audit does not treat design intent as implementation proof; every “clean” claim must point to code or test evidence.

## Verification Plan

- Use `rg`, `git diff`, `find`, `sed/nl`, and targeted tests where useful.
- Search for broad recursive scans (`read_tree_bytes`, `list_dir`, `find "$RO"`, wildcard materialization), legacy direct state paths, bypasses around FSM/outbox decisions, old compatibility flags/fallbacks, and direct service calls where a CLI/service adapter should be used.
- Validate and render the problem ledger after closure.

## Risks

- Some broad reads are valid explicit debug or runtime schema-loading paths; do not misclassify them as bugs without live-path context.
- Full repository search can produce noisy docs/tests; separate production code from tests/docs.
- If a confirmed gap is too large to fix inside the audit, create an explicit follow-up problem rather than hiding it.

## Assumptions

- Current branch `codex/reliable-evolution-fsm` reflects the latest intended architecture.
- The desired standard is no misleading half-migration: old code may exist only when clearly projection/debug/test-only or physically unreachable.
