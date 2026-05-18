# Finalize/session-ended generation ownership audit result

## Summary

Completed the finalize/session-ended generation ownership audit across inventory, repository mutation, outbox delivery, runtime handler enforcement, archive diagnostics, and aggregate regression coverage. The work was split into six child problems (`P334`-`P339`), and all are checked successful.

## Done

- `P334` / `R320` / `C341`: mapped finalize/session-ended/recovery/watchdog/restart/skill-end entry points and the identity fields they carry.
- `P335` / `R321` / `C342`: repository and pure FSM finalize generation boundaries now reject missing/non-positive generation before active clearing or pending restart mutation.
- `P336` / `R330` / `C351`: session-ended delivery payload construction, handler validation, SagaClient delivery, route schema, and repository mutation now fail closed on missing/invalid generation.
- `P337` / `R349` / `C371`: runtime session-ended/finalize handler enforcement closed across inventory, React contracts, Cortex mutation guards, recovery/compensation, and aggregate verification.
- `P338` / `R362` / `C385`: finalize reason, ended-at, and remaining stack archive diagnostics are bound to explicit scope/session/generation identity.
- `P339` / `R387` / `C413`: aggregate regression coverage closed the remaining stale compatibility residue, including follow-ups for every guard-discovered live generation issue.

## Verification

- Entry-point inventory was checked against broad `rg` searches and downstream targets were split instead of hidden.
- Repository/FSM focused tests passed after removing finalize generation fallback behavior.
- Session-ended delivery aggregate verification passed focused tests and source guards.
- Runtime handler aggregate verification passed 170 focused tests.
- Remaining stack/archive verification passed focused runtime and Cortex test suites, including 57, 61, 80, and 55 test subsets as recorded by `R362`.
- Final generation aggregate verification recorded runtime `147 passed`, additional focused suites, Cortex `21 passed`, final narrow guard with zero hits, and widened guard with all hits classified as non-session-authority.

## Known Gaps

- None for the P328/T324 acceptance criteria.
- Earlier child-level residuals such as upstream React generation defaults and cross-repo raw coercions were not accepted as permanent gaps; they were closed by later child/follow-up problems (`P337`, `P339`, `P385`, `P398`).
- Remaining widened guard hits are classified infrastructure counters, round numbers, audit/projection adapters, or generic FSM generation fields rather than live finalize/session-ended session-generation authority.

## Artifacts

- Child results/checks: `R320`/`C341`, `R321`/`C342`, `R330`/`C351`, `R349`/`C371`, `R362`/`C385`, `R387`/`C413`.
- Final guard artifacts: `.complex-problems/L20260516-222011/tmp/p401-narrow-guard-final.txt`, `.complex-problems/L20260516-222011/tmp/p401-widened-guard-final.txt`.
- Main implementation areas covered: `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, and `novaic-cortex/novaic_cortex`.
