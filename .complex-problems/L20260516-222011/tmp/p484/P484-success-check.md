# P484 Production side-effect callsite classification check

## Summary
P484 is solved. The one-go classification went beyond raw grep: it listed production call-site categories with file references, routed ambiguous items to downstream problems, and verified no source code changed.

## Evidence
- Raw targeted query artifact exists with `73` lines.
- Classification table covers service assembly, worker assembly, route factory assembly, generic task publish route, session outbox dispatcher, session-owned outbox effect writers/builders, worker effect executors, docs/examples, and saga-owned effect builders.
- Ambiguous/sensitive areas are routed to P485 (`/tasks/publish`) and P486 (`session_outbox.py` hardening).
- Before/after git status artifacts show no production source delta except the artifact header line.

## Criteria Map
- Production side-effect call sites listed with file references: satisfied by the classification table.
- Every listed call site classified: satisfied by category/rationale/route columns.
- Suspicious or ambiguous call sites identified: satisfied by P485/P486 routing.
- No source code changed: satisfied by before/after status comparison.

## Execution Map
- T477 was classified as read-only one-go.
- Execution ran targeted production scans for orchestrator, direct publish, and session outbox effect terms.
- Execution recorded classification and result artifacts.

## Stress Test
- Plausible failure mode: generic infrastructure is misclassified as stale bypass. The table separates generic adapter/worker boundaries from session-owned outbox effects.
- Plausible failure mode: sensitive direct calls are retained without follow-up. The table routes route publishing and session outbox hardening to dedicated child problems.

## Residual Risk
- Non-blocking: P484 does not itself clean or harden; P485/P486/P487 own those follow-up slices.

## Result IDs
- R473
