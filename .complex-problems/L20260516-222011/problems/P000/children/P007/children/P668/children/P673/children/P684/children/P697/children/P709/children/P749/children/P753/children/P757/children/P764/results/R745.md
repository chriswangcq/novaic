# Sandbox service residue discovery result

## Summary

Sandbox service and SDK source, tests, and README were scanned for stale local fallback, compatibility, direct materialize/writeback, mount caching, ownership, and Blob/LogicalFS boundary residue. One product-code remediation candidate was found: `sandbox_service/core/filesystem.py` contains unused filesystem diff/sanitize helpers that are only exported and tested, not used by active Sandbox service execution paths.

## Done

- Enumerated Sandbox service and SDK file surfaces under `novaic-sandbox-service` and `novaic-sandbox-sdk`.
- Searched for `legacy`, `compat`, `fallback`, `direct`, `bypass`, `base64`, `media`, `artifact`, `local`, `materialize`, `writeback`, `mount`, `cache`, `logicalfs`, `blob`, `sandbox`, `raw`, `TODO`, `FIXME`, `stub`, `commit`, `ro`, `rw`, and `sync`.
- Inspected high-signal files:
  - `novaic-sandbox-service/sandbox_service/core/filesystem.py`
  - `novaic-sandbox-service/sandbox_service/core/process.py`
  - `novaic-sandbox-service/sandbox_service/core/mount_namespace.py`
  - `novaic-sandbox-service/tests/test_sandbox_boundary.py`
  - `novaic-sandbox-sdk/sandbox_sdk/contracts.py`
  - `novaic-sandbox-sdk/README.md`
- Ran Sandbox SDK/service tests: `PYTHONPATH=novaic-sandbox-sdk:novaic-sandbox-service pytest -q novaic-sandbox-sdk/tests novaic-sandbox-service/tests`.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p764-sandbox-scan.txt`.
- Test result: `16 passed in 2.25s`.
- `tests/test_sandbox_boundary.py` verifies the Sandbox service does not import Cortex, Blob, or LogicalFS and does not contain workspace ownership terms in service code.
- `sandbox_sdk/contracts.py` uses base64 only as the JSON wire representation for stdout/stderr bytes; this is current service-boundary behavior, not artifact/base64 payload leakage to LLM context.
- `sandbox_service/core/process.py` and `core/mount_namespace.py` keep process execution and bind mount construction explicit and policy-free.
- `rg` shows `sandbox_service/core/filesystem.py` helpers are only referenced by tests and `sandbox_service/core/__init__.py`, not by the active service route or process runner.

## Known Gaps

- Remediation candidate: delete or relocate the unused Sandbox filesystem helper surface if no external import requires it:
  - `novaic-sandbox-service/sandbox_service/core/filesystem.py`
  - related exports in `novaic-sandbox-service/sandbox_service/core/__init__.py`
  - tests in `novaic-sandbox-service/tests/test_sandbox_core.py` that only exercise these helpers
- No product code was modified in this discovery child. The candidate should be handled by the later remediation branch.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p764-sandbox-scan.txt`
- pytest output: `16 passed in 2.25s`
