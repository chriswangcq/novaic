# Blob LogicalFS Sandbox VMuse service-code residue discovery result

## Summary

The split service-code residue discovery completed across Blob, LogicalFS, Sandbox, VMuse, and app resource/generated copies. Blob service had no active remediation candidate. LogicalFS, Sandbox, VMuse, and app copied resources produced exact cleanup candidates for the later remediation branch.

## Done

- Closed P762 / R743: Blob service residue discovery.
- Closed P763 / R744: LogicalFS residue discovery.
- Closed P764 / R745: Sandbox service residue discovery.
- Closed P765 / R746: VMuse service residue discovery.
- Closed P766 / R747: App resource copy residue discovery.

## Verification

- Blob service scan artifact: `.complex-problems/L20260516-222011/tmp/p762-blob-scan.txt`.
- LogicalFS scan artifact: `.complex-problems/L20260516-222011/tmp/p763-logicalfs-scan.txt`; tests passed: `10 passed in 0.32s`.
- Sandbox scan artifact: `.complex-problems/L20260516-222011/tmp/p764-sandbox-scan.txt`; tests passed: `16 passed in 2.25s`.
- VMuse scan artifact: `.complex-problems/L20260516-222011/tmp/p765-vmuse-scan.txt`; tests passed: `1 passed in 0.01s`.
- App resource scan artifact: `.complex-problems/L20260516-222011/tmp/p766-app-resource-scan.txt`.

## Known Gaps

- Remediation candidates for the later remediation branch:
  - LogicalFS public docs/metadata still over-emphasize snapshot/view/patch and should mention live `/ro` and `/rw` authority: `novaic-logicalfs/README.md`, `novaic-logicalfs/pyproject.toml`, `novaic-logicalfs/logicalfs/__init__.py`, `novaic-logicalfs/logicalfs/contracts.py`.
  - Sandbox has unused filesystem helper surface only referenced by tests/exports: `novaic-sandbox-service/sandbox_service/core/filesystem.py`, `novaic-sandbox-service/sandbox_service/core/__init__.py`, and helper-only tests in `novaic-sandbox-service/tests/test_sandbox_core.py`.
  - VMuse source has a stale FastMCP direct media entry path: `novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py`, FastMCP branches in `cli.py`, wording in `__init__.py`, and the console script path in `pyproject.toml`.
  - App resource/generated copies mirror the VMuse stale FastMCP path and must be synchronized when source VMuse is cleaned.
- No product code was modified in this discovery ticket.

## Artifacts

- R743
- R744
- R745
- R746
- R747
