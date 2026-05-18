# P625 Boundary Test Coverage Classification

## Covered

- SDK wire/client contract: `novaic-sandbox-sdk/tests/test_sandbox_sdk.py`.
- Cortex sandboxd/logicalfs shell wiring: `test_sandboxd_wiring.py`, `test_sandbox_requires_mount_namespace.py`, `test_shell_capabilities_internal_auth.py`.
- Cortex shell output/artifact projection: `test_shell_capabilities_blob_contract.py`, `test_tool_output_projection.py`, `test_step_result_projection.py`.
- Runtime shell output and no historical tool-image injection: `test_shell_output_contract.py`, `test_no_historical_tool_image_injection.py`.
- Runtime direct tool surface and migrated shell-capability boundary: `test_runtime_tool_path_contract.py`.
- Runtime bridge `/v1/internal/shell` explicit env: `test_runtime_explicit_contracts.py::test_cortex_bridge_shell_exec_sends_explicit_capability_env`.
- Runtime legacy/FSM/worker-supervision guardrails: `test_pr255_legacy_compat_cleanup.py`, `test_pr315_queue_fsm_final_residue_guard.py`, `test_pr343_runtime_worker_roster_ssot.py`.

## Results

- SDK + Cortex focused suite: 38 passed.
- Runtime focused suite from correct runtime cwd: 55 passed.

## Gaps

No blocking test coverage gap found for the SDK/runtime boundary. Generated `__pycache__` entries appeared in inventory because the inventory used `find` after tests; they are not source coverage gaps.
