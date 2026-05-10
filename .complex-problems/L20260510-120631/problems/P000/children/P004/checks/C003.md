# Check: P004 Cleanup Deploy Verify

## Verdict

Success.

## Evidence

- `scripts/run_all_tests.sh` includes `logicalfs` as a first-class test lane and includes `../novaic-logicalfs` in Cortex `PYTHONPATH`.
- `scripts/start.sh` includes `/opt/novaic/services/novaic-logicalfs` in Cortex `PYTHONPATH`.
- `deploy` syncs `novaic-logicalfs` before Cortex startup and the deploy lint now requires that wiring.
- Old skipped local-shell fallback tests and `NOVAIC_CORTEX_REAL_SANDBOXD_TESTS` skip gate were removed.
- `./scripts/run_all_tests.sh` passed all lanes.
- `./deploy services` succeeded and fresh-smoke verified all required logs.
- `./deploy status` shows all backend ports, worker roles, subscriber, and relay healthy.

## Criteria Map

- Scripts wire `novaic-logicalfs`: satisfied.
- Old Cortex materialization/diff/layout helper residue removed: satisfied for active code and old skipped fallback tests.
- Residue scans enforce dependency boundaries: satisfied.
- Full tests pass: satisfied.
- Deploy starts/fresh-smokes: satisfied.
- LogicalFS daemon status documented: satisfied; package-only is intentional in this phase.

## Execution Map

The deployed runtime now starts Cortex with `novaic-logicalfs` on `PYTHONPATH`; Cortex imports the substrate package, projects Workspace data into it, and sends sandboxd a mount-backed `SandboxExecSpec`.

## Stress Test

The standard test suite plus deploy fresh-smoke checked both source-level wiring and running service freshness. Removing skipped local-shell tests prevents the old fallback architecture from remaining as misleading executable documentation.

## Residual Risk

None blocking P004. A future LogicalFS daemon would be a new phase, not hidden unfinished work in this package-based extraction.
