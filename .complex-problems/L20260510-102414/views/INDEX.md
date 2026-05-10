# Complex Problem Ledger

Ledger: L20260510-102414
Schema: v6
Root: P000 - LogicalFS layering and module boundary cleanup
Status: done
Updated: 2026-05-10T02:33:24+00:00

## Problem Tree
- [done] P000: LogicalFS layering and module boundary cleanup
  - [done] P001: Audit current Cortex/Sandbox/LogicalFS/Blob layering
  - [done] P002: Extract module boundaries for shell capabilities, LogicalFS, and process execution
  - [done] P003: Make LogicalFS storage dependency explicit
  - [done] P004: Verify layering refactor and remove misleading residue

## Active

## Blocked

## Done
- [x] P000: LogicalFS layering and module boundary cleanup
- [x] P001: Audit current Cortex/Sandbox/LogicalFS/Blob layering
- [x] P002: Extract module boundaries for shell capabilities, LogicalFS, and process execution
- [x] P003: Make LogicalFS storage dependency explicit
- [x] P004: Verify layering refactor and remove misleading residue

## Tickets
- [done] T000: Audit and refactor Cortex shell layering boundaries -> P000 (split)
- [done] T001: Audit active shell layering and decide canonical model -> P001 (one_go)
- [done] T002: Extract shell capability, LogicalFS, and process execution modules -> P002 (one_go)
- [done] T003: Add explicit Workspace tree-byte port for LogicalFS -> P003 (one_go)
- [done] T004: Verify refactor and scan for misleading residue -> P004 (one_go)

## Latest Checks
- [success] C000: P001 Layering audit completed with canonical call/dependency model and concrete cleanup targets.
- [success] C001: P002 Shell capability, LogicalFS, and process execution modules extracted; sandbox.py is now the facade/orchestrator.
- [success] C002: P003 LogicalFS now consumes an explicit Workspace logical tree-byte port instead of private store internals.
- [success] C003: P004 Compile, targeted tests, full Cortex tests, and residue scans passed after the layering refactor.
- [success] C004: P000 LogicalFS layering clarified and physically refactored; tests and residue scans passed.
