# Sandbox service residue discovery check

## Summary

Success. Result R745 solves P764 because it discovered and scanned Sandbox service/SDK surfaces, classified the high-signal hits, ran the focused Sandbox test suite, and listed exact remediation candidates without modifying product code.

## Evidence

- R745 records the scan artifact `.complex-problems/L20260516-222011/tmp/p764-sandbox-scan.txt`.
- R745 cites inspected files across service core, SDK contracts, SDK README, and boundary tests.
- R745 records `PYTHONPATH=novaic-sandbox-sdk:novaic-sandbox-service pytest -q novaic-sandbox-sdk/tests novaic-sandbox-service/tests` with `16 passed in 2.25s`.
- R745 records an exact product-code cleanup candidate for the unused filesystem helper surface.

## Criteria Map

- Criterion: Sandbox service/source files are discovered and scanned with bounded commands.
  Evidence: R745 Done items 1-2 and scan artifact.
- Criterion: Suspicious hits are classified as current execution isolation behavior, adapter boundary, stale residue, or unrelated vocabulary.
  Evidence: R745 Verification classifies process/mount code as current, SDK base64 as wire-byte encoding, boundary tests as guardrails, and filesystem helper exports as stale cleanup candidates.
- Criterion: Exact remediation candidates are listed, or absence is explicitly recorded.
  Evidence: R745 Known Gaps lists `core/filesystem.py`, related `core/__init__.py` exports, and helper-only tests.
- Criterion: No product code is modified in this discovery child.
  Evidence: R745 Known Gaps states no product code was modified.

## Execution Map

- Ticket T755 was classified one_go because this was a bounded single execution-layer discovery task.
- Execution scanned files, inspected representative code, checked active references, and ran tests.
- Result R745 recorded both current boundary confirmations and cleanup candidates.

## Stress Test

- Plausible failure mode: base64 use in SDK contracts could be mistaken for LLM context base64 leakage.
- Check result: R745 distinguishes internal JSON wire encoding for stdout/stderr bytes from artifact/image payload exposure.
- Plausible failure mode: mount/process/local terms could be over-flagged.
- Check result: R745 treats process and mount namespace code as current Sandbox execution responsibility, while only flagging helper code that is not consumed by active execution paths.

## Residual Risk

- Low and non-blocking for P764. Discovery is complete; cleanup remains for a later remediation branch.

## Result IDs

- R745
