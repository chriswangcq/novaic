# Business test residue discovery

## Summary

Scanned Business test-like files with bounded commands and spot-read high-signal hits. No product code was modified. Most suspicious terms are intentional guard coverage around removed routes, explicit dependency boundaries, and dispatch behavior. One existing source-code remediation candidate from P756 remains outside this test-only child: `business/internal/message.py` wording.

Evidence:
- Test discovery found the Business test suite under `novaic-business/tests/`, including dispatch, IM aggregation, device binding, retired routes, environment repository, and schema boundary tests.
- Focused residue output is saved at `.complex-problems/L20260516-222011/tmp/p760-business-test-scan.txt`.
- `novaic-business/tests/test_pr141_compat_cleanup.py` intentionally guards retired Business device proxy routes and retired health stub routes.
- `novaic-business/tests/test_pr151_device_binding_contract.py` intentionally guards the canonical device binding shape.
- `novaic-business/tests/test_pr157_device_vm_prep_actions.py` intentionally proves Business owns VM prep action orchestration and routes to the hardware API.
- `novaic-business/tests/test_im_aggregation.py` uses explicit `IMAggregationConfig` injection in `_subscriber`; environment monkeypatches are retained as input fixture context for config-related behavior, not as hidden business decision reads.
- `novaic-business/tests/test_dispatch_subscriber.py` intentionally exercises dispatch source claims, Queue dispatch, idempotency, and subscriber/Cortex boundary guardrails.

Classification:
- `compat`, `retired`, `not registered`, and old route names in `test_pr141_compat_cleanup.py` are deletion guards.
- `direct` in dispatch subscriber docstrings and tests refers to direct unit invocation of private methods or direct sync dispatch assertions, not an active direct LLM tool or Gateway bypass.
- `fallback` in IM aggregation/docstrings is mostly product behavior/kill-switch vocabulary, not a hidden runtime fallback branch in the active grouping decision.
- Device terms in `test_pr151_device_binding_contract.py` and `test_pr157_device_vm_prep_actions.py` are current Business-to-Device boundary tests.

No stale Business test remediation candidate was found in this pass.
