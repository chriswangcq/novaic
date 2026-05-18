# Classify runtime continuity and context.read residue

## Problem Definition

Runtime still contains `read_context`, `context.read`, cross-wake, idempotency, and continuity-looking paths. These paths must be classified so safe side paths remain understandable and active stale fallbacks do not survive behind the new prepared-snapshot provider path.

## Proposed Solution

Map the runtime context-read handler, runtime wake/input handlers, and bridge call sites. Classify each residue as active-safe, dead/stale, or risky. Fix any active stale path that can influence provider input, or split it into a smaller child problem if it requires independent remediation.

## Acceptance Criteria

- `context_handlers.py`, `runtime_handlers.py`, and bridge/context-read callers are mapped with evidence pointers.
- Each remaining `read_context`, `context.read`, continuity, cross-wake, or historical context path is classified.
- Any active stale provider-input path is fixed or split.
- Focused tests/static guards are identified and run.

## Verification Plan

Use `rg` to inventory residue, inspect mapped call sites, then run context-read, no-wake-replay, explicit skill summary, prepare-context guardrail, and runtime explicit contract tests.

## Risks

- Some residue is intentionally safe (notification hints, by-id context views); over-deleting would break user-visible history tools.
- Some residue may only be referenced indirectly through topics, so source search must include handlers, sagas, tests, and topic names.

## Assumptions

- Provider-message authority has already been guarded by `P160` and `P161`; this ticket focuses on remaining non-provider or questionable residue.
