# P020 Ticket - Assembly DSL Shrink Verification

## Problem Definition

P018/P019 introduced and used helper-backed worker assembly, but the parent assembly gap is only closed if the repository proves the business assembly surface is actually thinner and old worker lifecycle construction does not remain protected by tests or alternate paths.

## Proposed Solution

Perform an explicit shrink verification pass for worker assembly.

The verification should:

- Search for direct lifecycle-construction residue in `worker_assemblies.py`.
- Confirm helper substrate is the only place where generic worker construction primitives are used.
- Run the full focused assembly/effect/outbox test slice.
- Compile worker modules.
- Record line-count and residue evidence.
- If a gap remains, create a follow-up instead of marking success.

## Acceptance Criteria

- `worker_assemblies.py` has no direct worker lifecycle primitive construction.
- Helper-backed assembly tests pass.
- Outbox assembly tests pass.
- Effect boundary tests pass.
- Compile checks pass.
- Evidence is recorded in the ledger.

## Verification Plan

- Run `rg` residue checks for worker lifecycle primitives.
- Run focused pytest suite across task/saga/health/scheduler/outbox/helper/boundary tests.
- Run compileall on worker modules.
- Run `wc -l` to capture current assembly/helper size.

## Risks

- A text-only residue check can miss dynamic indirection; focused behavior tests must run as well.
- Some remaining code may be valid business wiring rather than lifecycle residue; classify based on explicit dependency boundary.

## Assumptions

- P018 and P019 code is already present in the working tree.
