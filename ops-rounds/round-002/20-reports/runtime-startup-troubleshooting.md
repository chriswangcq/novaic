# Runtime Startup Troubleshooting (Round 002)

## Scope
Runtime Orchestrator startup and `/api/health` readiness failures observed during Round 002 validation.

## Known Failure Signatures

### Signature A: Contract health test timeout
- Symptom:
  - `Runtime Orchestrator /api/health did not become healthy within 45s`
- First observed in:
  - `tests/contract/test_runtime_orchestrator_process_startup.py::TestRuntimeOrchestratorProcessHealth::test_runtime_orchestrator_process_health`
  - `tests/contract/test_runtime_orchestrator_process_startup.py::TestGatewayStartsWithRuntimeOrchestrator::test_gateway_starts_and_proxies_internal_with_runtime_orchestrator`
- Effect:
  - Blocks Gate C (`Runtime startup healthcheck issue resolved and verified`)

### Signature B: Manual subprocess repro unhealthy
- Repro command exits with:
  - `final healthy False return None`
- Meaning:
  - Subprocess remains alive, but health endpoint polling does not succeed within timeout window

## Reproduction Commands

1) Contract-level startup test:
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py::TestRuntimeOrchestratorProcessHealth::test_runtime_orchestrator_process_health -q`

2) Combined contract smoke:
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py tests/contract/test_internal_api_contract_baseline.py`

3) Manual subprocess repro:
- `python -u - <<'PY' ... main_novaic.py runtime-orchestrator ... /api/health polling ... PY`

## Current Assessment
- Runtime lifecycle consistency baseline is improved.
- Startup healthcheck instability root cause is identified and fixed in contract probe path (`trust_env=False` for localhost checks).
- Repeat-run startup verification is completed (3/3 pass). See:
  - `ops-rounds/round-002/20-reports/runtime-startup-verification-report.md`

## Next Debug Actions
- Continue monitoring startup contract in CI and daily round checks.
- If regression reappears, re-enable subprocess log capture path and compare against known signatures.
