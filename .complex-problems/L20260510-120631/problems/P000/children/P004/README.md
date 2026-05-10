# Clean old LogicalFS residue and wire scripts/deploy/tests

## Problem

After the new LogicalFS boundary works, old Cortex-owned helpers, stale imports, misleading docs, and missing deployment/test wiring would make the codebase ambiguous.

## Success Criteria

- `scripts/start.sh`, `deploy`, and `scripts/run_all_tests.sh` include `novaic-logicalfs` explicitly where needed.
- Old Cortex materialization/diff/layout helper residue is removed.
- Residue scans enforce that `novaic-logicalfs` imports no forbidden product/service modules and Cortex imports no sandbox core.
- Full tests pass.
- If LogicalFS is implemented as a daemon, deployment starts and fresh-smokes it; if package-only, docs/checks explain why no daemon exists yet.
