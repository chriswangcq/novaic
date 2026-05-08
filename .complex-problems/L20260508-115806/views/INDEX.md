# Complex Problem Ledger

Ledger: L20260508-115806
Schema: v6
Root: P000 - 补齐 FSM 基建与业务 DSL 全部 gap
Status: doing
Updated: 2026-05-08T05:15:17+00:00

## Problem Tree
- [done] P000: 补齐 FSM 基建与业务 DSL 全部 gap
  - [done] P001: Action engine effect-plan DSL
    - [done] P008: Effect plan substrate contracts
    - [done] P009: Task and saga engines use effect adapters
      - [done] P012: Task engine effect adapter migration
      - [done] P013: Saga engine effect adapter migration
      - [done] P014: Task/saga engine boundary guards
    - [done] P010: Health and scheduler engines use effect adapters
      - [done] P015: Health engine effect adapter migration
      - [done] P016: Scheduler engine effect adapter migration
      - [done] P017: Health/scheduler boundary guards
    - [done] P011: Effect-plan boundary tests
  - [done] P002: Declarative worker assembly DSL shrink
    - [done] P018: Generic worker assembly helper substrate
    - [done] P019: Migrate worker assemblies to helper substrate
    - [done] P020: Assembly DSL shrink verification
  - [done] P003: Effect adapter and assembly guardrails
  - [done] P004: Docs status consistency lint
  - [done] P005: Timestamp-aware deploy smoke
  - [done] P006: Runtime worker supervision
  - [done] P007: Final residue closure and verification

## Active

## Blocked

## Done
- [x] P000: 补齐 FSM 基建与业务 DSL 全部 gap
- [x] P001: Action engine effect-plan DSL
- [x] P002: Declarative worker assembly DSL shrink
- [x] P003: Effect adapter and assembly guardrails
- [x] P004: Docs status consistency lint
- [x] P005: Timestamp-aware deploy smoke
- [x] P006: Runtime worker supervision
- [x] P007: Final residue closure and verification
- [x] P008: Effect plan substrate contracts
- [x] P009: Task and saga engines use effect adapters
- [x] P010: Health and scheduler engines use effect adapters
- [x] P011: Effect-plan boundary tests
- [x] P012: Task engine effect adapter migration
- [x] P013: Saga engine effect adapter migration
- [x] P014: Task/saga engine boundary guards
- [x] P015: Health engine effect adapter migration
- [x] P016: Scheduler engine effect adapter migration
- [x] P017: Health/scheduler boundary guards
- [x] P018: Generic worker assembly helper substrate
- [x] P019: Migrate worker assemblies to helper substrate
- [x] P020: Assembly DSL shrink verification

## Tickets
- [done] T000: Close all FSM substrate and business DSL gaps -> P000 (split)
- [done] T001: Action engine effect-plan DSL -> P001 (split)
- [done] T002: Effect plan substrate contracts -> P008 (one_go)
- [done] T003: Task and Saga Engines Use Effect Adapters -> P009 (split)
- [done] T004: Task Engine Effect Adapter Migration -> P012 (one_go)
- [done] T005: Saga Engine Effect Adapter Migration -> P013 (one_go)
- [done] T006: Task/Saga Engine Boundary Guards -> P014 (one_go)
- [done] T007: Health and Scheduler Engines Use Effect Adapters -> P010 (split)
- [done] T008: Health Engine Effect Adapter Migration -> P015 (one_go)
- [done] T009: Scheduler Engine Effect Adapter Migration -> P016 (one_go)
- [done] T010: Health/Scheduler Boundary Guards -> P017 (one_go)
- [done] T011: Effect-Plan Boundary Tests -> P011 (one_go)
- [done] T012: Declarative Worker Assembly DSL Shrink -> P002 (split)
- [done] T013: Generic Worker Assembly Helper Substrate -> P018 (one_go)
- [done] T014: P019 Ticket - Migrate Worker Assemblies To Helper Substrate -> P019 (one_go)
- [done] T015: P020 Ticket - Assembly DSL Shrink Verification -> P020 (one_go)
- [done] T016: P003 Ticket - Effect Adapter And Assembly Guardrails -> P003 (one_go)
- [done] T017: P004 Ticket - Docs Status Consistency Lint -> P004 (one_go)
- [done] T018: Timestamp-aware deploy smoke -> P005 (one_go)
- [done] T019: Runtime worker supervision -> P006 (one_go)
- [done] T020: Final residue closure and verification -> P007 (one_go)

## Latest Checks
- [success] C011: P018 P018 is solved. The generic helper substrate exists, is business-agnostic, and is verified for generic, concurrent, and synthetic worker assembly shapes.
- [success] C012: P019 P019 is solved. Concrete worker assemblies no longer own worker lifecycle construction. They use the generic helper substrate and keep only explicit business wiring, adapters, handlers, and startup metadata.
- [success] C013: P020 P020 is solved. The assembly shrink is not only implemented but verified: old lifecycle constructor residue is absent from `worker_assemblies.py`, tests now guard the helper-backed shape, and focused behavior/boundary checks pass.
- [success] C014: P002 P002 is solved. Worker assembly has a reusable helper substrate, all target worker assemblies use it, and residue checks prove the old direct lifecycle-construction path is gone from `worker_assemblies.py`.
- [success] C015: P003 P003 is solved. Guardrail tests now protect both action-engine effect boundaries and worker assembly helper boundaries.
- [success] C016: P004 P004 is solved. The known stale PR-338 docs status is corrected, and CI now has a narrow status-consistency lint to prevent that drift from returning.
- [success] C017: P005 P005 is solved. Deploy restart is no longer verified only by stale tail/process evidence: restart captures a remote epoch, runs fresh-log smoke after startup, and exposes the same timestamp-aware check as `./deploy fresh-smoke [epoch]`. CI now guards the deploy hook, command, critical logs, docs, and workflow wiring.
- [success] C018: P006 P006 is solved. Required runtime worker roles are now explicit in production startup and deploy status. The system no longer accepts a vague worker aggregate as sufficient evidence for role-level worker health.
- [success] C019: P007 P007 is solved. Final audit did not merely rubber-stamp the previous changes: it found and closed direct HTTP-client residue plus a stale lifecycle lint contract. Full runtime tests and the root lint chain now pass after those fixes.
- [success] C020: P000 The root problem is solved for the stated FSM substrate + business DSL closure scope. All seven child problems are success-checked, the root result is recorded, full Runtime tests pass, root lints pass, and final audit found and fixed additional residue instead of hiding it.
