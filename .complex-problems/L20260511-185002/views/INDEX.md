# Complex Problem Ledger

Ledger: L20260511-185002
Schema: v6
Root: P000 - Audit and fix shell CLIs to obey blob artifact contract
Status: done
Updated: 2026-05-11T11:19:35+00:00

## Problem Tree
- [done] P000: Audit and fix shell CLIs to obey blob artifact contract
  - [done] P001: Inventory shell CLI surfaces and blob-contract risks
  - [done] P002: Fix devicectl artifact-producing commands to use blob contract
  - [done] P003: Audit and fix agentctl and cortex CLI outputs
    - [done] P005: Audit and fix agentctl CLI Blob contract
    - [done] P006: Audit and fix cortex CLI Blob contract
  - [done] P004: Verify CLI blob contract and clean residual old behavior
    - [done] P007: Clean stale CLI artifact Blob namespace fixtures
    - [done] P008: Final CLI Blob contract verification

## Active

## Blocked

## Done
- [x] P000: Audit and fix shell CLIs to obey blob artifact contract
- [x] P001: Inventory shell CLI surfaces and blob-contract risks
- [x] P002: Fix devicectl artifact-producing commands to use blob contract
- [x] P003: Audit and fix agentctl and cortex CLI outputs
- [x] P004: Verify CLI blob contract and clean residual old behavior
- [x] P005: Audit and fix agentctl CLI Blob contract
- [x] P006: Audit and fix cortex CLI Blob contract
- [x] P007: Clean stale CLI artifact Blob namespace fixtures
- [x] P008: Final CLI Blob contract verification

## Tickets
- [done] T000: Split CLI blob contract remediation by command surface -> P000 (split)
- [done] T001: Inventory shell capability CLIs -> P001 (one_go)
- [done] T002: Wrap devicectl artifact outputs with Blob-backed tool-output.v1 -> P002 (one_go)
- [done] T003: Audit agentctl and cortex CLI output contracts -> P003 (split)
- [done] T004: Audit agentctl shell CLI output contract -> P005 (one_go)
- [done] T005: Audit cortex payload CLI output contract -> P006 (one_go)
- [done] T006: Verify CLI Blob contract and remove residual old behavior -> P004 (split)
- [done] T007: Replace stale device-screenshot artifact namespace fixtures -> P007 (one_go)
- [done] T008: Final CLI Blob contract verification pass -> P008 (one_go)

## Latest Checks
- [success] C000: P001 Success. The shell CLI surfaces are inventoried and the live blob-contract risks are identified with code evidence.
- [success] C001: P002 P002 is solved by R001. The two artifact-producing `devicectl` commands have direct code coverage and now produce Blob-backed `tool-output.v1` manifests instead of raw base64 stdout.
- [success] C002: P005 P005 is solved by R002. The active `agentctl` CLI paths were inspected and verified with targeted tests; no raw binary or base64 artifact stdout path was found.
- [success] C003: P006 P006 is solved by R003. The active `cortex payload` CLI paths are bounded text-inspection/interpretation APIs and do not emit raw binary artifacts inline.
- [success] C004: P003 P003 is solved by R004. The split child audits verified `agentctl` and `cortex` CLI output contracts separately, and neither family has an active raw artifact stdout path.
- [success] C005: P007 P007 is solved by R005. The stale `device-screenshot` namespace was removed from CLI/tool-output contract tests and replaced with `runtime-artifact`.
- [success] C006: P008 P008 is solved by R006. The verification evidence is strong enough: generated CLIs compile, focused tests pass on both repos, residual scans classify remaining Blob URI examples, and ledger validation succeeds.
- [success] C007: P004 P004 is solved by R007. Residual old behavior was cleaned and final verification passed with evidence from P007/P008.
- [success] C008: P000 P000 is solved by R008. The CLI surfaces were inventoried, active artifact-producing violations were fixed, non-artifact CLI families were audited, stale contract residue was cleaned, and focused verification passed.
