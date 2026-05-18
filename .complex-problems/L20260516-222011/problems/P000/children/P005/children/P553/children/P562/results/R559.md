# Cortex Materialization And Local Fallback Residue Inventory Result

## Summary

P562 is complete through three child classifications: materialization APIs (P566), shell/local execution fallback (P567), and stable/temp path compatibility residue (P568 with P569 evidence closure). The only high-confidence Cortex remediation candidate is `Workspace.materialize()` plus its legacy global `/rw/scratch` layout and tests.

## Done

- P566 classified Cortex materialization/direct file-authority hits.
  - Risky/removable: `Workspace.materialize()` and the legacy root `/rw/scratch` layout.
  - No production caller of `Workspace.materialize()` was found; callers are tests only.
  - Direct `_files` access inside `Workspace` is accepted as internal Workspace authority implementation for this audit.
- P567 classified shell fallback and executor bypass hits.
  - No production local shell fallback found.
  - Production wires `SandboxdClient`; missing executor fails explicitly.
  - Subprocess hits are test-only shell capability checks.
- P568 classified stable/temp path compatibility residue.
  - Stable `/cortex` mount is intended.
  - `novaic-cortex-sandbox-*` backing paths are rejected before execution.
  - No active old compatibility fallback or path adapter found.
- P569 added the missing exact command manifest for P568 reproducibility.

## Verification

- Child results:
  - P566/R555
  - P567/R556
  - P568/R557
  - P569/R558
- Child success checks:
  - P566 closed successfully before this rollup.
  - P567 closed successfully before this rollup.
  - P568 initially failed on missing command manifest, then closed successfully after P569.
- Evidence artifacts:
  - `.complex-problems/L20260516-222011/tmp/p566/materialize-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p566/materialize-slices.txt`
  - `.complex-problems/L20260516-222011/tmp/p567/shell-fallback-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p567/shell-fallback-slices.txt`
  - `.complex-problems/L20260516-222011/tmp/p568/path-compat-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p568/path-compat-slices.txt`
  - `.complex-problems/L20260516-222011/tmp/p568/scan-command-manifest.md`

## Known Gaps

- P554 should remove or replace `Workspace.materialize()`, remove the legacy root `/rw/scratch` layout if no other P553 child proves an active need, and update/delete `test_workspace_materialize.py`.
- No shell fallback remediation candidate from P567.
- No stable-path compatibility remediation candidate from P568.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p562-result.md`
