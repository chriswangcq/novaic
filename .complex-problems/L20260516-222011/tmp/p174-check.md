# Runtime wake continuity residue classification check

## Summary

`P174` is solved. Runtime wake continuity residue is classified as active-safe: runtime no longer synthesizes historical continuity or wake replay; it records current explicit inputs and uses generation-checked attach for active wakes. Verification also found and fixed a test hidden-cwd dependency.

## Evidence

- Runtime says cross-wake continuity is Cortex-owned at `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py:18-26`.
- `session.init` creates agent root/wake child and writes current explicit inputs at `runtime_handlers.py:70-149`.
- Current-turn message ids are registered/claimed at `runtime_handlers.py:170-195`.
- `session.attach_input` validates expected wake and generation at `runtime_handlers.py:240-276` before appending at `runtime_handlers.py:278-289`.
- No-wake-replay, generation-checked attach, active inbox, child-scope, explicit summary, recovery boundary, and prepare-context tests passed with `35 passed`.

## Criteria Map

- Runtime wake/session call sites mapped: satisfied.
- Cross-wake/idempotency/replay residues classified: satisfied as active-safe; retired replay producers absent.
- Focused guard tests identified/run: satisfied.
- Stale provider-input or old-message replay fixed/split: no active stale path found; one test hidden cwd input fixed.

## Execution Map

- `T161` one-go executed after parent split.
- Initial verification found a cwd-sensitive test.
- Fixed test path boundary and reran successfully.
- Recorded result `R156`.

## Stress Test

If attach loses generation/wake checking, generation attach tests fail. If runtime reintroduces wake replay markers or context-body replay, PR-113 and PR-85 guardrails fail. If recovery-boundary static checks depend on invocation cwd again, the repaired test remains stable from the monorepo root.

## Residual Risk

- Full caller inventory for `read_context` remains sibling `P175`.

## Result IDs

- R156
