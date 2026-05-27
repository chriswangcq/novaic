# Complex Problem Ledger

Ledger: L20260527-082839
Schema: v6
Root: P000 - Deploy reasoning streaming through Release Controller CI/CD
Status: doing
Updated: 2026-05-27T00:41:13+00:00

## Problem Tree
- [todo] P000: Deploy reasoning streaming through Release Controller CI/CD
  - [done] P001: Discover Release Controller deployment contract and current status
    - [done] P005: Inspect local Release Controller contract
    - [done] P006: Probe live Release Controller status and runs
  - [todo] P002: Commit and push deployable source state
    - [done] P007: Run final pre-push focused verification
    - [done] P008: Commit and push touched subrepos
    - [doing] P009: Commit and push root submodule pointers and deployment ledger
  - [todo] P003: Trigger Release Controller server deployment and observe run completion
  - [todo] P004: Verify published server health and close deployment evidence

## Active
- [ ] P000: Deploy reasoning streaming through Release Controller CI/CD (todo)
- [ ] P002: Commit and push deployable source state (todo)
- [ ] P003: Trigger Release Controller server deployment and observe run completion (todo)
- [ ] P004: Verify published server health and close deployment evidence (todo)
- [ ] P009: Commit and push root submodule pointers and deployment ledger (doing)

## Blocked

## Done
- [x] P001: Discover Release Controller deployment contract and current status
- [x] P005: Inspect local Release Controller contract
- [x] P006: Probe live Release Controller status and runs
- [x] P007: Run final pre-push focused verification
- [x] P008: Commit and push touched subrepos

## Tickets
- [splitting] T000: Release Controller deployment execution plan -> P000 (split)
- [done] T001: Discover controller contract through docs/config and live status -> P001 (split)
- [done] T002: Read local Release Controller docs and config -> P005 (one_go)
- [done] T003: Probe live controller read APIs -> P006 (one_go)
- [splitting] T004: Commit and push source for Release Controller deployment -> P002 (split)
- [done] T005: Run focused pre-push checks -> P007 (one_go)
- [done] T006: Commit and push touched submodule repositories -> P008 (one_go)
- [executing] T007: Commit root release pointer state -> P009 (one_go)

## Latest Checks
- [success] C000: P005 P005 is solved by R000. Local Release Controller contract is clear enough to proceed to live probing and later trigger: `main` branch releases to `staging` through `/v1/triggers`, prod is promotion-only, and direct deploy scripts are controller internals.
- [success] C001: P006 P006 is solved by R001. The live controller is reachable, healthy, and has known current release pointers. Later deployment can use host-local `POST /v1/triggers` via SSH.
- [success] C002: P001 P001 is solved by R002. The controller contract and live status are known, including exact trigger path and current release baseline.
- [success] C003: P007 P007 is solved by R003. Fresh focused tests passed in all touched repos and dirty files are known for explicit staging.
- [success] C004: P008 P008 is solved by R004. All touched subrepos are committed, pushed, and clean.
