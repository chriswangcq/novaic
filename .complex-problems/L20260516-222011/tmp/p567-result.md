# P567 Result: Cortex Shell Fallback And Executor Bypass Classification

## Summary

Classified Cortex shell fallback and executor bypass hits. No production local shell fallback was found in Cortex. The production path wires `SandboxdClient`, and the runtime explicitly fails when no sandbox executor is configured. Subprocess hits are confined to tests for generated CLI/capability scripts.

## Done

- Recorded scan output:
  - `.complex-problems/L20260516-222011/tmp/p567/shell-fallback-scan.txt`
- Recorded line-numbered source slices:
  - `.complex-problems/L20260516-222011/tmp/p567/shell-fallback-slices.txt`
- Classified hits:
  - Intended production wiring: `main_cortex.py` installs `SandboxdClient`.
  - Intended failure guard: `api.py` / `sandbox.py` reject missing sandbox executor.
  - Intended test doubles: `test_sandboxd_wiring.py` fake runners.
  - Intended test subprocess: shell capability script tests.

## Verification

- `novaic-cortex/novaic_cortex/main_cortex.py:98` wires `SandboxdClient(cli_args.sandboxd_url)`.
- `novaic-cortex/novaic_cortex/api.py:62` raises when sandbox executor factory is not configured.
- `novaic-cortex/novaic_cortex/sandbox.py:81-90` returns explicit error if `sandbox_executor is None`.
- `novaic-cortex/novaic_cortex/sandbox.py:114-122` executes through `self.sandbox_executor.execute(SandboxExecSpec(...))`.
- `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py` asserts there is no local fallback without sandboxd executor.
- No production `subprocess`, `Popen`, or `os.system` shell execution path was found under `novaic-cortex/novaic_cortex`.

## Known Gaps

- No Cortex shell fallback remediation candidate from this child.
- P568 still needs to classify path compatibility residue separately.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p567/shell-fallback-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p567/shell-fallback-slices.txt`
