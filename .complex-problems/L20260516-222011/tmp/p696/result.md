# Result: P696 Foundational file and sandbox service boundary classification

## Summary
The foundational file/sandbox boundary track is complete for current-state classification and safe residue cleanup. Blob is classified as cheap byte/object storage, LogicalFS as the realtime logical RO/RW substrate/library currently used by Cortex rather than a standalone service, and Sandbox/Sandboxd as the execution layer rather than the file-authority layer. Safe active residue found during the scan was remediated and verified.

## Completed Child Problems
- P699 / R686 / C729: Blob service boundary map. Blob owns byte/object storage and artifact transport; it is not the realtime workspace authority and not Cortex semantic state.
- P700 / R687 / C730: LogicalFS boundary map. LogicalFS is the realtime logical RO/RW substrate today, implemented as a library/substrate rather than a standalone service process.
- P701 / R688 / C731: Sandbox and Sandboxd boundary map. Sandboxd owns process execution; SDK/core/facade responsibilities are separated from Cortex orchestration and LogicalFS view semantics.
- P702 / R691 / C734: Foundational residue cleanup. Two active cleanup candidates were patched and verified; no active P703 cleanup candidate remains.

## Evidence
- `.complex-problems/L20260516-222011/tmp/p699/boundary-map.md`
- `.complex-problems/L20260516-222011/tmp/p700/boundary-map.md`
- `.complex-problems/L20260516-222011/tmp/p701/boundary-map.md`
- `.complex-problems/L20260516-222011/tmp/p702/result.md`
- `.complex-problems/L20260516-222011/tmp/p704/lint-blob-workspace-boundary.txt`
- `.complex-problems/L20260516-222011/tmp/p704/retired-phrase-scan.txt`

## Verification
- Blob/LogicalFS guard: `python3 scripts/ci/lint_blob_workspace_boundary.py` passed.
- LogicalFS tests: `cd novaic-logicalfs && PYTHONPATH=.:../novaic-common:../novaic-blob-service python3 -m pytest -q` passed with 10 tests.
- Sandbox SDK tests: `cd novaic-sandbox-sdk && PYTHONPATH=.:../novaic-common python3 -m pytest -q` passed with 3 tests.
- Sandbox service tests: `cd novaic-sandbox-service && PYTHONPATH=.:../novaic-sandbox-sdk:../novaic-common python3 -m pytest -q` passed with 13 tests.
- Targeted py_compile checks were run for LogicalFS, Cortex adapter, and sandbox files in their child problems.

## Decisions
- Do not pretend LogicalFS is already a standalone server. The honest current state is substrate/library with a service-extraction gap.
- Do not collapse Sandboxd into Cortex. Cortex owns semantic scope/context/shell orchestration; Sandboxd owns process execution.
- Do not treat Blob as realtime workspace state. Blob remains cheap byte/object storage; LogicalFS is the realtime file authority layer above it.

## Residual Gaps
- Standalone LogicalFS service extraction remains outside P696. This is an architecture direction, not a current residue failure.
- Semantic/app/device service boundaries remain for the sibling P697 track.
- Broader service-entrypoint cleanup remains for the sibling P698 track.
