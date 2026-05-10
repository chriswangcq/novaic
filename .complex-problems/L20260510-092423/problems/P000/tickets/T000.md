# Design Full Logical RO/RW Shell Contract

## Problem Definition

Shell commands are dynamic and cannot be analyzed reliably from the outer command string. The RO/RW optimization design must therefore preserve a complete logical filesystem view and move performance optimization below that boundary. RW conflict reduction should be handled through directory conventions rather than a full concurrency protocol in this phase.

## Proposed Solution

Produce a corrected architecture design covering:

- shell-visible semantic contract;
- RW directory convention;
- injected environment variables;
- agent/subagent write behavior protocol;
- mount/cache substrate choices;
- staged implementation plan;
- tests and invariants.

## Acceptance Criteria

- The design rejects command-string semantic guessing as a correctness mechanism.
- The design keeps `/cortex/ro` and `/cortex/rw` complete and stable from shell perspective.
- The design defines `/cortex/rw/public`, `/cortex/rw/subagents/<id>`, and `/cortex/rw/tmp/<exec-id>`.
- The design explains how cache/mirror/manifest can optimize without changing semantics.
- The design includes follow-up tickets and non-goals.

## Verification Plan

- Cross-check against the current sandbox materialization code.
- Ensure the design can be implemented incrementally.
- Record a problem-level success check against all criteria.

## Risks

- A "complete logical view" without FUSE may still require eager projection unless a mirror/cache exists.
- Directory convention reduces conflict frequency but does not enforce hard isolation.

## Assumptions

- Concurrency protocol is out of scope for this design pass.
- Same-agent subagents are a team boundary, not a mutual distrust boundary.
