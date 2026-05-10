# Complex Problem Ledger

Ledger: L20260510-192637
Schema: v6
Root: P000 - Cortex State Authority Remediation Plan
Status: done
Updated: 2026-05-10T11:34:45+00:00

## Problem Tree
- [done] P000: Cortex State Authority Remediation Plan
  - [done] P001: State Authority Taxonomy And Storage Rules
  - [done] P002: Active Stack And Status Projection Remediation
  - [done] P003: Scope Transition Log Remediation
  - [done] P004: Blob Payload Authority Contract
  - [done] P005: LogicalFS Snapshot Patch Versus Live Filesystem
  - [done] P006: Process Cache Config And Documentation Residue Cleanup

## Active

## Blocked

## Done
- [x] P000: Cortex State Authority Remediation Plan
- [x] P001: State Authority Taxonomy And Storage Rules
- [x] P002: Active Stack And Status Projection Remediation
- [x] P003: Scope Transition Log Remediation
- [x] P004: Blob Payload Authority Contract
- [x] P005: LogicalFS Snapshot Patch Versus Live Filesystem
- [x] P006: Process Cache Config And Documentation Residue Cleanup

## Tickets
- [done] T000: Split Cortex State Authority Remediation Into Per-Plane Designs -> P000 (split)
- [done] T001: Design Explicit State Authority Taxonomy -> P001 (one_go)
- [done] T002: Design Event Backed Active Stack Status -> P002 (one_go)
- [done] T003: Design Scope Transition Log Replacement -> P003 (one_go)
- [done] T004: Design Blob Payload Authority Contract -> P004 (one_go)
- [done] T005: Design LogicalFS Live State Direction -> P005 (one_go)
- [done] T006: Design Process Cache Config And Documentation Cleanup -> P006 (one_go)

## Latest Checks
- [success] C000: P001 State taxonomy defines allowed authorities for LogicalFS, SQLite, Redis, Blob, and memory.
- [success] C001: P002 Active stack/status plan moves runtime authority to SQLite events/projections and demotes Workspace files to traces.
- [success] C002: P003 Scope transition local NDJSON is replaced by SQLite lifecycle events with optional exporter.
- [success] C003: P004 Blob remains raw byte authority while semantic manifests live in SQLite/Workspace.
- [success] C004: P005 LogicalFS target is live per-operation durability; snapshot/patch is transitional.
- [success] C005: P006 Process memory is allowed only for rebuildable cache/config/client wiring; docs and stale lock prose should be cleaned.
- [success] C006: P000 Each audited state-authority gap has a concrete remediation plan and storage role.
