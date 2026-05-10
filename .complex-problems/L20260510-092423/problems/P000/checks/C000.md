# Full Logical RO/RW Shell Contract Design Check

## Summary

Success. The design corrects the earlier optimization direction: shell-visible RO/RW semantics are complete and stable, command-string prediction is rejected as a correctness boundary, RW conflict frequency is reduced through directory convention, and implementation phases are staged below the visible filesystem contract.

## Evidence

- R000 defines the corrected shell-visible RO/RW contract.
- R000 defines `/cortex/rw/public`, `/cortex/rw/subagents/<id>`, `/cortex/rw/tmp/<exec-id>`, and supporting env vars.
- R000 defines agent behavior conventions for self/public/tmp writes.
- R000 defines the implementation substrate: persistent mirror, manifest, content-addressed cache, temp exec tree, and write journal.
- R000 lists staged implementation phases, tests, invariants, non-goals, and follow-up tickets.
- R000 cites current code points that must change or be demoted.

## Criteria Map

- Corrected semantic contract for shell-visible RO/RW -> R000 sections 1 and 7.
- RW directory layout and env vars -> R000 sections 2 and 3.
- Agent behavior conventions -> R000 section 4.
- Implementation substrate preserving complete logical view -> R000 section 5.
- Staged implementation plan, tests, invariants -> R000 sections 6, 7, 9, 10.
- Explicit out of scope -> R000 section 8.

## Execution Map

- T000 -> R000: design-only execution with no runtime behavior changes.

## Stress Test

- Failure mode: script accesses RO without the outer command containing `$RO`. Result: R000 forbids command-string semantic gating and requires complete logical RO/RW.
- Failure mode: subagents accidentally overwrite each other's files. Result: R000 defines `$RW_SELF`, `$RW_PUBLIC`, and `$RW_TMP` conventions to reduce default collision.
- Failure mode: cache causes stale logical view. Result: R000 requires manifest validation and safe rebuild/fail-closed behavior.
- Failure mode: design accidentally promises ACL isolation. Result: R000 explicitly marks hard subagent ACL isolation as non-goal.

## Residual Risk

- Non-blocking: this is design only; implementation and benchmarking remain follow-up tickets.
- Non-blocking: directory convention reduces conflicts but does not eliminate all conflicting writes.

## Result IDs

- R000

## Blocking Gaps

- none
