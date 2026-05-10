# Check: Root LogicalFS Extraction

## Verdict

Success.

## Evidence

- `novaic-logicalfs` exists as a dedicated substrate package with snapshot/view/patch contracts and local materialization/diff provider.
- Cortex imports `logicalfs` and `sandbox_sdk`; Cortex does not import `sandbox_core`.
- sandboxd service remains the process-execution boundary over `sandbox_core`.
- The active shell path is tested with a fake runner that inspects the LogicalFS source root, mutates RW, and verifies Workspace patch persistence.
- `scripts/run_all_tests.sh`, `scripts/start.sh`, and `deploy` explicitly include `novaic-logicalfs`.
- Stale local-shell fallback tests and skip gate were physically removed.
- `./scripts/run_all_tests.sh` passed all 16 lanes.
- `./deploy services` and `./deploy status` passed.

## Criteria Map

- Business-agnostic LogicalFS substrate: satisfied by P001.
- Cortex adapter only owns Cortex semantics: satisfied by P002.
- Shell execution path goes through LogicalFS view and sandboxd: satisfied by P003.
- Old residue cleaned and operational wiring deployed: satisfied by P004.

## Execution Map

The current architecture is:

```text
Cortex Workspace
  -> Cortex LogicalFS adapter
  -> novaic-logicalfs snapshot/view/patch substrate
  -> sandbox_sdk SandboxExecSpec
  -> sandboxd service
  -> sandbox_core process/mount substrate
  -> LogicalFS patch observation
  -> Cortex Workspace write-back
```

LogicalFS does not know Cortex, agent identity, shell capability semantics, sandboxd, or business code.

## Stress Test

The closure combined unit tests, focused integration-style boundary tests, full monorepo test matrix, deploy fresh-smoke, and runtime status verification. This catches the prior failure mode where code existed but scripts/deploy still followed an old path.

## Residual Risk

No blocking residual risk for the package-based final state. If the product later wants a standalone LogicalFS server, that should be opened as a new phase rather than treated as unfinished work in this extraction.
