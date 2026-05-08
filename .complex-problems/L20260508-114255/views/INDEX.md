# Complex Problem Ledger

Ledger: L20260508-114255
Schema: v6
Root: P000 - 全面审核当前 FSM 基建与业务 DSL 设计 gap
Status: doing
Updated: 2026-05-08T03:56:19+00:00

## Problem Tree
- [done] P000: 全面审核当前 FSM 基建与业务 DSL 设计 gap
  - [done] P001: Audit generic FSM worker substrate boundaries
  - [done] P002: Audit business DSL worker layer
  - [done] P003: Audit runtime wiring deployment and old-path residue
  - [done] P004: Audit verification guardrails and docs alignment

## Active

## Blocked

## Done
- [x] P000: 全面审核当前 FSM 基建与业务 DSL 设计 gap
- [x] P001: Audit generic FSM worker substrate boundaries
- [x] P002: Audit business DSL worker layer
- [x] P003: Audit runtime wiring deployment and old-path residue
- [x] P004: Audit verification guardrails and docs alignment

## Tickets
- [done] T000: Full FSM And Business DSL Gap Audit -> P000 (split)
- [done] T001: Audit Generic FSM Worker Substrate Boundaries -> P001 (one_go)
- [done] T002: Audit business DSL worker layer -> P002 (one_go)
- [done] T003: Audit runtime wiring deployment and old-path residue -> P003 (one_go)
- [done] T004: Audit verification guardrails and docs alignment -> P004 (one_go)

## Latest Checks
- [success] C000: P001 Core FSM/worker substrate is business-agnostic; remaining gap is thick imperative assembly rather than declarative worker DSL.
- [success] C001: P002 Handler layer is a thin typed DSL boundary; action engines remain imperative effect/protocol adapters.
- [success] C002: P003 Runtime and deployment use unified main_novaic.py worker modes; retired worker files are absent; remaining gaps are ops hardening and stale comments/logs.
- [success] C003: P004 Tests protect current FSM/worker substrate and thin handlers; missing guardrails remain for pure effect-plan engines, assembly thinness, deploy-log freshness, and docs status consistency.
- [success] C004: P000 Full audit complete: real FSM/worker substrate and thin handler migration achieved; strict business-only DSL still has action-engine and assembly gaps.
