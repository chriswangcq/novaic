# P480 Imperative dispatch residue inventory check

## Summary
P480 is solved as an inventory child. The one-go execution produced raw guard artifacts, a classification matrix, downstream cleanup candidates, and a before/after production status check.

## Evidence
- R472 saved `.complex-problems/L20260516-222011/tmp/p480/imperative-dispatch-residue-raw-guards.txt` with `1078` raw guard lines.
- R472 saved `.complex-problems/L20260516-222011/tmp/p480/imperative-dispatch-residue-classification.md` with required boundary, test/docs guard, high-confidence removable residue, and ambiguous/downstream candidate sections.
- The classification records file references for service/worker assembly, saga topics, session outbox dispatcher, session repository outbox writes, worker effect executors, route publishing, and FSM generation validation.
- `git-status-before.txt` and `git-status-after.txt` match except for the header line, showing no production source delta was introduced by this inventory child.

## Criteria Map
- Saved guard artifact lists searched patterns and matching files: satisfied by the raw guard artifact.
- Each hit bucket is classified: satisfied by the classification matrix.
- Inventory records enough file references for downstream cleanup: satisfied by required-boundary and downstream-candidate sections.
- No production code changed: satisfied by before/after status comparison.

## Execution Map
- T475 was classified one-go because it was bounded read-only inventory.
- Execution ran four guard groups: saga orchestration, direct publish/side effects, active-session/session mutation vocabulary, and finalize/session-ended/generation compatibility vocabulary.
- Execution spot-checked representative production hits before recording R472.

## Stress Test
- Plausible failure mode: a one-go inventory could be shallow and only save raw grep output. The result avoids that by adding a classification matrix and downstream candidates.
- Plausible failure mode: inventory accidentally edits source. The before/after production status check guards against that.

## Residual Risk
- Non-blocking: P480 intentionally does not remove code. Direct side-effect and finalize/session compatibility cleanup remain explicit child problems P481 and P482, with P483 reserved for final verification.

## Result IDs
- R472
