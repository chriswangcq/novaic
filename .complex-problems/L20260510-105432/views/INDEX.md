# Complex Problem Ledger

Ledger: L20260510-105432
Schema: v6
Root: P000 - Extract stable sandbox infrastructure into base modules
Status: done
Updated: 2026-05-10T03:02:05+00:00

## Problem Tree
- [done] P000: Extract stable sandbox infrastructure into base modules
  - [done] P001: Audit generic versus Cortex-specific sandbox pieces
  - [done] P002: Implement common sandbox infrastructure modules
  - [done] P003: Migrate Cortex to common sandbox infrastructure
  - [done] P004: Verify base extraction and residue cleanup

## Active

## Blocked

## Done
- [x] P000: Extract stable sandbox infrastructure into base modules
- [x] P001: Audit generic versus Cortex-specific sandbox pieces
- [x] P002: Implement common sandbox infrastructure modules
- [x] P003: Migrate Cortex to common sandbox infrastructure
- [x] P004: Verify base extraction and residue cleanup

## Tickets
- [done] T000: Promote stable sandbox primitives into common base modules -> P000 (split)
- [done] T001: Classify stable sandbox primitives -> P001 (one_go)
- [done] T002: Build common sandbox modules -> P002 (one_go)
- [done] T003: Migrate Cortex sandbox code to common primitives -> P003 (one_go)
- [done] T004: Verify common extraction and residue cleanup -> P004 (one_go)

## Latest Checks
- [success] C000: P001 Generic sandbox primitives classified; Cortex-specific LogicalFS semantics protected from over-extraction.
- [success] C001: P002 common.sandbox base modules implemented and covered by targeted tests.
- [success] C002: P003 Cortex migrated to common sandbox process, mount namespace, and filesystem primitives; local process runner removed.
- [success] C003: P004 Common and Cortex tests pass; residue scan confirms Cortex uses common sandbox primitives without local duplicates.
- [success] C004: P000 Stable sandbox process, mount namespace, and filesystem primitives extracted into common and Cortex migrated to use them.
