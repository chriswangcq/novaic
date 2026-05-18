# Attach generation contract inventory result

## Summary

Completed the read-only attach generation inventory. Runtime attach and session outbox publish paths are strict, repository attach-race behavior buffers stale input, and no active no-generation attach delivery path was found. One hardening candidate remains: `build_attach_input_effect()` should reject missing/non-positive `expected_session_generation` instead of relying on caller/outbox validation.

## Done

- Saved raw attach/generation guard output and file list.
- Classified runtime validation, durable outbox boundary, repository race guard, tests, and one hardening candidate.
- Made no source changes.

## Verification

- Raw artifact exists at `.complex-problems/L20260516-222011/tmp/p496/attach-generation-raw-guards.txt` with `1312` lines.
- Classification artifact exists at `.complex-problems/L20260516-222011/tmp/p496/attach-generation-classification.md`.

## Known Gaps

- P497 should tighten `build_attach_input_effect()` generation validation.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p496/attach-generation-raw-guards.txt`
- `.complex-problems/L20260516-222011/tmp/p496/attach-generation-files.txt`
- `.complex-problems/L20260516-222011/tmp/p496/attach-generation-classification.md`
