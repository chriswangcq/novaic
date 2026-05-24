# Complex Problem Ledger

Ledger: L20260524-150426
Schema: v6
Root: P000 - Make release-controller non-conservative by default
Status: done
Updated: 2026-05-24T07:19:14+00:00

## Problem Tree
- [done] P000: Make release-controller non-conservative by default
  - [done] P001: Make source defaults and docs non-conservative
  - [done] P002: Activate non-conservative runtime policy on API host

## Active

## Blocked

## Done
- [x] P000: Make release-controller non-conservative by default
- [x] P001: Make source defaults and docs non-conservative
- [x] P002: Activate non-conservative runtime policy on API host

## Tickets
- [done] T000: Switch release-controller to real execution by default -> P000 (split)
- [done] T001: Update source defaults for real staging releases -> P001 (one_go)
- [done] T002: Activate API-host non-dry-run runtime default -> P002 (one_go)

## Latest Checks
- [success] C000: P001 Source defaults and docs now make release-controller non-conservative by default.
- [success] C001: P002 API-host release-controller now defaults to real execution and proved omitted-dry-run plus autonomous poll releases.
- [success] C002: P000 Release-controller is now cleanly non-conservative by default.
