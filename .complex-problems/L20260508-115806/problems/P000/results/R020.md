# Root result: FSM substrate and business DSL gap closure

## Summary

Closed the planned FSM substrate + business DSL gap set through seven tickets. The implementation now has explicit action effect plans, a reusable worker assembly substrate, guardrails for effect boundaries and assembly thickness, docs/deploy/status supervision lints, and final residue cleanup.

## Done

- P001: Action engines now use explicit decision/effect plan boundaries and concrete effect adapters.
- P002: Worker assembly was shrunk through `assembly_helpers.py` and declarative worker runtime builders.
- P003: Guardrails now enforce action engine boundaries, effect adapters, and worker assembly delegation.
- P004: Docs/roadmap status drift is guarded by `lint_docs_status_consistency.py`.
- P005: Deploy restart now captures a remote timestamp and runs timestamp-aware fresh-log smoke.
- P006: Production start/status now supervise exact runtime worker role counts.
- P007: Final audit found and fixed direct HTTP client residue and stale lifecycle lint drift; full Runtime tests and root lint chain pass.

## Verification

- Runtime full test suite: `pytest -q` in `novaic-agent-runtime` -> `530 passed`.
- Focused runtime/FSM/worker sweeps:
  - `38 passed`
  - `103 passed`
  - `136 passed`
  - `14 passed`
  - `13 passed`
- Root lint chain passed:
  - dispatch/httpx/internal-async/lifecycle/subagent/scope/message/chat/wake/cortex/retired/frontend/agent-loop/entangled/docs/deploy/start/agent-main/retired-agent/lifecycle-owner lints.
- Compile:
  - Cortex, Runtime, and CI scripts compile successfully.
- Diff hygiene:
  - Root, Runtime, and Cortex `git diff --check` pass.
- Residue scans:
  - No raw worker constructors remain in `worker_assemblies.py`.
  - No direct `httpx.Client`/`httpx.AsyncClient` remains in Runtime/Cortex.
  - Coarse deploy worker count and stale subscriber log hint were removed from live deploy/start paths.

## Known Gaps

- No remote production deploy was run in this closure pass.
- LLM Factory and Business provider HTTP allowlist entries remain visible in `lint_httpx.sh`; they are outside this Runtime FSM/business DSL closure scope.

## Artifacts

- `.complex-problems/L20260508-115806`
- `novaic-agent-runtime/queue_service/worker/effects.py`
- `novaic-agent-runtime/task_queue/workers/*_effects.py`
- `novaic-agent-runtime/task_queue/workers/assembly_helpers.py`
- `novaic-agent-runtime/task_queue/workers/worker_assemblies.py`
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
- `novaic-cortex/novaic_cortex/blob_payload.py`
- `novaic-cortex/novaic_cortex/blob_store.py`
- `deploy`
- `scripts/start.sh`
- `scripts/ci/lint_deploy_fresh_smoke.py`
- `scripts/ci/lint_runtime_worker_supervision.py`
- `scripts/ci/lint_docs_status_consistency.py`
- `scripts/ci/lint_httpx.sh`
- `scripts/ci/lint_lifecycle_loop_ownership.sh`
- `docs/runbooks/deploy.md`
- `docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md`
