# Implement Pure DSL Runtime Closure

## Problem

The previous audit proved the runtime is live on the new FSM/worker/roster path and has no active old session/FSM branch, but it is not pure DSL yet. The remaining gaps are hand-written worker assemblies, action engines that execute effects directly, callback-heavy saga/action policy code, handler registry metadata gaps, CI bytecode hygiene, and architecture documentation that must honestly reflect the current state.

Implement the full remediation backlog from `.complex-problems/L20260508-165336/artifacts/P004-result.md`:

- DSL-001 Worker Assembly Spec Substrate
- DSL-002 Plan-First Action Engine Contract
- DSL-003 Task Execution Policy Tables
- DSL-004 Saga Launch and Saga Definition Purity
- DSL-005 Scheduler and Health Action Specs
- DSL-006 Business Handler Registry Review
- DSL-007 CI Guard Hygiene
- DSL-008 Pure DSL Architecture Status Document

This implementation must preserve the already-live FSM/worker/roster path and avoid reintroducing old branches.

## Success Criteria

- Worker process assembly is driven by explicit component specs rather than duplicated per-worker lifecycle construction.
- Action engines no longer call `execute_effect(...)` directly; effect execution is owned by a generic runner/substrate.
- Task execution policy behavior has explicit decision/policy units with deterministic tests.
- Saga launch and saga definitions expose deterministic plan/compile boundaries while keeping real computation as named extension points.
- Scheduler and health actions expose plan/spec boundaries and direct effect execution is removed from engines.
- Handler registry exposes declarative metadata and tests prevent lifecycle/runtime ownership from leaking into handlers.
- CI guard hygiene prevents Python bytecode generation from breaking generated-artifact checks.
- Documentation or durable design notes state the implemented architecture and the remaining accepted boundaries honestly.
- Old displaced code paths are deleted or guarded; no parallel hidden implementation remains.
- Repository checks, targeted tests, architecture guards, generated-artifact guard, ledger validate/render/status, and focused diff review all pass.
