# Runtime Shell Handler SDK Wiring Result

## Summary

Audited active runtime shell handler wiring. Runtime does not import or invoke `sandbox_sdk` directly; it calls Cortex `/v1/internal/shell` through `CortexBridge.shell_exec`, and Cortex owns the sandboxd SDK dependency. No active runtime shell-handler local execution bypass was found.

## Done

- Recorded runtime shell/SDK scan in `.complex-problems/L20260516-222011/tmp/p626-runtime-sdk-wiring-scan.txt`.
- Recorded clean source/test slices in `.complex-problems/L20260516-222011/tmp/p626-runtime-sdk-wiring-evidence.txt`.
- Classified active path and risky-looking hits in `.complex-problems/L20260516-222011/tmp/p626-runtime-sdk-wiring-classification.md`.
- Ran focused runtime tests.

## Verification

- `python -m pytest novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py::test_cortex_bridge_shell_exec_sends_explicit_capability_env -q` passed: 7 tests.

## Known Gaps

- `main_novaic.py` subprocess supervision is outside active shell-handler wiring and remains assigned to P627 residue classification.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p626-runtime-sdk-wiring-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p626-runtime-sdk-wiring-evidence.txt`
- `.complex-problems/L20260516-222011/tmp/p626-runtime-sdk-wiring-classification.md`
- `.complex-problems/L20260516-222011/tmp/p626-runtime-sdk-wiring-tests.txt`
