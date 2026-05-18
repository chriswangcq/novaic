# Final Guard Classification Result

## Summary

Completed P504. I reran the final imperative-dispatch guard sweep over `novaic-agent-runtime`, saved raw guard outputs, separated production hits from test/docs guard hits, and produced a classification matrix. No dangerous unclassified production dispatch bypass was found, but P505 has three high-confidence cleanup candidates.

## Done

- Saved broad raw guard outputs for direct saga creation, direct queue publish, legacy/fallback/compat terms, active-session pointer terms, attach generation, and finalize/session-ended terms.
- Generated production-only guard outputs and hit counts.
- Classified production hits as required adapter/dispatcher/worker boundaries, intended FSM/outbox effect construction, strict validation paths, or small cleanup candidates.
- Confirmed no production code was intentionally changed in this inventory child.

## Verification

- Raw all-scope hit counts: `.complex-problems/L20260516-222011/tmp/p504/hit-counts.tsv`.
- Production-only hit counts: `.complex-problems/L20260516-222011/tmp/p504/production-hit-counts.tsv`.
- Classification matrix: `.complex-problems/L20260516-222011/tmp/p504/final-guard-classification.md`.
- Production diff snapshot before classification: `.complex-problems/L20260516-222011/tmp/p504/runtime-diff-before-classification.txt`.

## Known Gaps

- P505 should remove the unused `task_queue/constants.py` module.
- P505 should remove the stale `task_queue/client.py` deprecated polling separator comment.
- P505 should tighten `SessionRepository.session_ended` typing so `remaining_stack` is not shaped as optional while immediately required.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p504/guard-commands-and-scope.md`
- `.complex-problems/L20260516-222011/tmp/p504/direct-saga-create-production.txt`
- `.complex-problems/L20260516-222011/tmp/p504/direct-queue-publish-production.txt`
- `.complex-problems/L20260516-222011/tmp/p504/legacy-fallback-compat-production.txt`
- `.complex-problems/L20260516-222011/tmp/p504/active-session-pointer-production.txt`
- `.complex-problems/L20260516-222011/tmp/p504/attach-generation-production.txt`
- `.complex-problems/L20260516-222011/tmp/p504/finalize-session-ended-production.txt`
- `.complex-problems/L20260516-222011/tmp/p504/final-guard-classification.md`
