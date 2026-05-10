# Tool shell boundary design satisfies requested design scope

## Summary

The result solves the requested design-only problem. It provides a detailed unified model for keeping only `shell`, `display`, `skill_begin`, `skill_end`, and `sleep` outside shell; moving environment interface tools inside shell capabilities; and using bounded text plus artifact/resource URIs as the durable tool output contract.

## Evidence

- Result `R000` defines the outside-shell primitive set and explains why each item belongs there.
- Result `R000` lists shell-inside capability families: IM, subagent, device, blob/file, payload/Cortex data, runtime inspection, and business/environment APIs.
- Result `R000` defines `ToolOutputV1` with bounded text, artifacts, URIs, source metadata, access hints, projection policy, retention, and diagnostics.
- Result `R000` defines Cortex, current-turn LLM, monitor UI, display, and storage projections.
- Result `R000` includes flows for IM read/reply, device screenshot, subagent coordination, and payload/large log handling.
- Result `R000` includes invariants, failure modes, safety/audit controls, migration phases, and non-goals.
- Runtime code was not changed.

## Criteria Map

- Detailed shell-inside/shell-outside boundary -> covered by sections 2, 3, and 4 of `R000`.
- Concrete output envelope -> covered by section 5 of `R000`.
- Display role -> covered by section 3 and projection rules in section 6 of `R000`.
- Skill/sleep role -> covered by section 4 of `R000`.
- Cortex/LLM/monitor/files/blob interactions -> covered by sections 6, 7, and 8 of `R000`.
- Invariants, failure modes, migration phases, non-goals -> covered by sections 10, 11, 12, and 13 of `R000`.
- Design-only/no code changes -> verified by the result's scope and current ledger actions.

## Execution Map

- Ticket `T000` was classified `one_go` because the deliverable was one bounded design artifact.
- Result `R000` recorded the system design and design verification.
- No child problems or implementation tickets were needed for this design-only request.

## Stress Test

- Failure mode: design accidentally keeps IM/subagent as harness tools. The result explicitly moves them inside shell capabilities.
- Failure mode: design collapses display into shell and loses explicit perception. The result keeps `display` outside shell and defines it as perception.
- Failure mode: tool output still allows prompt bloat. The result requires manifest-only history and no durable raw sensory bytes.
- Failure mode: shell becomes unsafe escape hatch. The result requires scoped tokens, audit, idempotency, command schemas, bounded output, and permission classes.

## Residual Risk

- Non-blocking: exact CLI names and concrete schema files remain implementation-phase work.
- Non-blocking: security policy details need later code-level tickets.
- Non-blocking: implementation may discover compatibility cleanup complexity, but the requested design is complete.

## Result IDs

- R000
