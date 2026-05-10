# Check: P031 Full Cutover Verification

## Result IDs

- R027

## Verdict

success

## Criteria Map

- `Full Cortex test suite passes.` Met: `355 passed`.
- `LogicalFS and sandbox-service targeted suites still pass.` Met: LogicalFS `10 passed`; sandbox-service `13 passed`.
- `Residue scans show no old direct live constructor patterns in Cortex source/tests.` Met for old constructors. The only broad Workspace match is the helper's `Workspace(authority, agent_id, ...)`.
- `Shell/sandbox RO/RW wiring tests pass.` Met through the sandbox-service boundary/service tests and Cortex sandbox wiring tests included in the full Cortex suite.
- `Any remaining old store modules are classified for P024 cleanup rather than silently accepted.` Met. R027 lists the old file, policy allowlist, and docs residue that P024 must delete or rewrite.

## Execution Map

- Ran full Cortex tests.
- Ran LogicalFS tests.
- Ran sandbox-service tests.
- Ran residue scans for old constructors, old authority names, old BlobCortexStore names, deleted module imports, and object API references.

## Stress Test

The scan intentionally included docs and tests, not only live source, to catch misleading residue. It found several non-runtime residues, which are explicitly carried into P024 cleanup rather than hidden.

## Residual Risk

P031 proves the cutover path is connected and test-passing, but it does not physically delete old authority files or stale docs. P024 remains open and is mandatory before declaring the root problem clean.
