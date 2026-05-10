# Complex Problem Ledger

Ledger: L20260510-110352
Schema: v6
Root: P000 - Extract sandbox execution into an independent base service
Status: done
Updated: 2026-05-10T03:25:21+00:00

## Problem Tree
- [done] P000: Extract sandbox execution into an independent base service
  - [done] P001: Sandboxd common contract and client
  - [done] P002: Sandboxd independent service
  - [done] P003: Cortex uses sandboxd on the active server path
  - [done] P004: Deployment and service registry include sandboxd
  - [done] P005: Remove stale in-process sandbox execution residue
  - [done] P006: End-to-end verification of sandboxd extraction

## Active

## Blocked

## Done
- [x] P000: Extract sandbox execution into an independent base service
- [x] P001: Sandboxd common contract and client
- [x] P002: Sandboxd independent service
- [x] P003: Cortex uses sandboxd on the active server path
- [x] P004: Deployment and service registry include sandboxd
- [x] P005: Remove stale in-process sandbox execution residue
- [x] P006: End-to-end verification of sandboxd extraction

## Tickets
- [done] T000: Build sandboxd service and migrate Cortex execution to it -> P000 (split)
- [done] T001: Implement sandboxd common contract and runner client -> P001 (one_go)
- [done] T002: Build novaic-sandbox-service -> P002 (one_go)
- [done] T003: Wire Cortex active server path to sandboxd -> P003 (one_go)
- [done] T004: Register and deploy sandboxd as a first-class backend service -> P004 (one_go)
- [done] T005: Clean stale in-process sandbox residue -> P005 (one_go)
- [done] T006: Verify sandboxd extraction end to end -> P006 (one_go)

## Latest Checks
- [success] C000: P001 Common sandboxd contract/client completed and verified.
- [success] C001: P002 Independent sandboxd service implemented and verified.
- [success] C002: P003 Cortex server path now wires shell execution through sandboxd runner port.
- [success] C003: P004 Sandboxd is registered in config/start/deploy/status/log smoke paths.
- [success] C004: P005 Stale Cortex command-wrapping path removed; direct runner is explicit test/library adapter.
- [success] C005: P006 Sandboxd extraction verified locally across contract, service, Cortex wiring, deployment scripts, and residue scans; remote deploy smoke remains operational.
- [success] C006: P000 Sandbox execution extracted into independent sandboxd service in code/start/deploy wiring; local verification passed; remote deploy smoke remains operational.
