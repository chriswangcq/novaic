# Repair chained agent-loop stall defects

## Problem Definition

The production agent loop stalls because a shell capability internal-auth failure cascades into missing tool `step_ref` projection and then failed `wake_finalize` compensation. The code must be repaired at the real runtime boundaries so the same chain cannot recur.

## Proposed Solution

Split the repair into targeted child problems:

1. Shell capability Cortex internal-auth boundary: pass the Cortex internal key from runtime to sandbox capability env and make `agentctl` include `X-Internal-Key` for Cortex internal APIs.
2. Context event projection step-ref contract: ensure `ToolStepRecorded` projects a top-level `step_ref` for LLM expansion.
3. Saga compensation finalize context: preserve root/path/session generation/stack metadata when creating `wake_finalize` compensation.

Each child problem must include regression tests proving the repaired contract.

## Acceptance Criteria

- `agentctl im read` and other Cortex-backed shell capabilities can call Cortex internal endpoints without 401 when runtime has the internal key.
- LLM context snapshots created from `ToolStepRecorded` include top-level `step_ref` for every tool message with a payload ref.
- Failed wake/think/actions sagas create `wake_finalize` compensation with enough context to archive the wake scope and call `session_ended` against the correct session generation.
- Existing tests plus targeted new regressions pass.
- No fallback path hides the bug by silently swallowing auth or finalize failures.

## Verification Plan

- Add focused unit tests for shell capability env/header behavior.
- Add context projection regression tests for top-level `step_ref`.
- Add saga compensation regression tests verifying context preservation.
- Run targeted test suites for `novaic-cortex` and `novaic-agent-runtime`.

## Risks

- Passing internal keys into shell capability env increases sensitivity of the shell environment; only the explicit sandbox capability allowlist should carry it, and it must not be printed by default.
- Compensation context must preserve enough metadata without inventing fallback values that hide upstream context loss.
- Existing production stuck state may still need deployment/recovery verification after code repair.

## Assumptions

- Cortex internal endpoints intentionally require `X-Internal-Key`; shell capability commands are trusted runtime-injected CLI tools and may receive that key through explicit capability env.
- The current `step_ref` expansion contract is correct; the projection is the broken layer.
- The saga context already contains root/path/session metadata on normal paths; compensation must copy it instead of narrowing the context.
