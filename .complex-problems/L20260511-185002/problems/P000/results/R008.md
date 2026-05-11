# shell CLI Blob artifact contract completed

## Summary

Completed the full CLI Blob contract audit and repair. The only active artifact-producing CLI violations were `devicectl hd screenshot` and `devicectl hd file-pull`; both now upload bytes to Blob Service and print `tool-output.v1` manifests. Agentctl and cortex CLI families were audited and verified. Residual stale fixture namespaces were cleaned.

## Done

- P001 inventoried shell CLI surfaces and risk areas.
- P002 fixed `devicectl` artifact-producing commands.
- P003 audited `agentctl` and `cortex` command families through P005/P006.
- P004 cleaned residual old behavior and ran final verification through P007/P008.
- Updated runtime artifact examples to `blob://runtime-artifact/...`.
- Updated old payload fixture from `blob://payload/1` to `blob://cortex-payload/1`.

## Verification

- Generated `agentctl`, `cortex`, and `devicectl` scripts compile.
- Cortex focused tests passed:
  - `21 passed` for initial devicectl/tool-output/blob suite.
  - `47 passed` for final shell/blob/context suite.
  - `30 passed` after residual payload fixture cleanup.
- Agent-runtime focused tests passed:
  - `16 passed` for initial agentctl/runtime contract suite.
  - `19 passed` for final runtime contract suite.
- `device-screenshot` scan returned no matches in affected trees.
- Ledger validation succeeded.

## Known Gaps

- No known CLI Blob contract gaps remain in the audited command surfaces.
- Full monorepo test suite was not run; this was intentionally focused on CLI Blob contract paths.
- Deployment has not been performed in this work package.

## Artifacts

- `novaic-cortex/novaic_cortex/shell_capabilities.py`
- `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`
- `novaic-cortex/tests/test_tool_output_projection.py`
- `novaic-cortex/tests/test_operational_store.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py`
- Ledger: `.complex-problems/L20260511-185002`
