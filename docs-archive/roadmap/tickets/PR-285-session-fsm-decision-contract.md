# PR-285 — Session FSM Decision Contract

Status: Closed

## Goal

Promote the pure session decision from "action only" to a real FSM transition:
given explicit input state and event, it returns next state plus intended
effects.

## Scope

- Extend dispatch/finalize decision dataclasses with next-state information.
- Represent intended side effects as typed effect specs.
- Keep the pure decision free of DB, Queue, Saga, time, uuid, env, and globals.
- Update repository code to consume the new decision contract without adding
  hidden inputs.

## Dependencies

- PR-283 state taxonomy.
- PR-284 event vocabulary.

## Risks

- Partial adoption could create a misleading "FSM-looking" wrapper around old
  imperative branches.
- Return contract changes may ripple into route and assembler expectations.

## Acceptance Criteria

- Pure decision outputs `action`, `next_status`, and typed `effects`.
- Repository no longer reconstructs core next-state intent independently.
- Tests assert deterministic decision output from explicit inputs.

## Verification

- Targeted FSM contract tests.
- Existing dispatch/finalize tests.

## Closure Notes

- Added `SessionEffectType` and `SessionEffectSpec`.
- Extended dispatch/finalize decisions with `next_status` and typed intended
  `effects`.
- Pure start-wake decisions now declare `starting` as next state and a
  `create_wake` effect.
- Pure attach/buffer/finalize decisions declare their next status and intended
  effects without DB/Saga/Queue access.
- Added `tests/test_pr285_session_fsm_decision_contract.py`.
- Verified with targeted FSM/finalize tests: 14 passed.
