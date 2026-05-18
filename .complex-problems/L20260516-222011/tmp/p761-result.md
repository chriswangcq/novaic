# Device test residue discovery

## Summary

Scanned Device test-like files with bounded commands and spot-read high-signal hits. No stale Device test remediation candidate was found, and no product code was modified.

Evidence:
- Test discovery found `novaic-device/tests/test_device_explicit_boundary_contracts.py`, `test_pr194_schema_push_fail_fast.py`, `test_pr120_no_device_entangled_cli.py`, `test_pr141_no_common_auth_db_param.py`, `test_pr157_device_vm_prep_actions.py`, and `test_pr151_device_binding_contract.py`.
- Focused residue output is saved at `.complex-problems/L20260516-222011/tmp/p761-device-test-scan.txt`.
- `test_pr120_no_device_entangled_cli.py` intentionally guards deletion of retired direct-Entangled CLI/config branches.
- `test_pr151_device_binding_contract.py` intentionally verifies the canonical `mounted_tools` object shape and rejects retired binding paths.
- `test_pr157_device_vm_prep_actions.py` intentionally verifies Device exposes VM prep through hardware execution actions.
- `test_device_explicit_boundary_contracts.py` intentionally verifies explicit Business proxy/schema contracts and rejects implicit request builders.

Classification:
- `direct` in `test_pr120_no_device_entangled_cli.py` is a retired-CLI deletion guard.
- `screenshot` in `test_pr151_device_binding_contract.py` is an example mounted tool name inside the current canonical object shape; it is not an inline media route expectation.
- Device/Business terms in `test_device_explicit_boundary_contracts.py` are explicit boundary contract tests.
- No stale inline `/vms/{id}/screenshot` route, base64 media payload expectation, or Gateway-owned device path was found in Device tests.

No stale Device test remediation candidate was found in this pass.
