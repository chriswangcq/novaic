# shell CLI Blob artifact contract final check

## Summary

P000 is solved by R008. The CLI surfaces were inventoried, active artifact-producing violations were fixed, non-artifact CLI families were audited, stale contract residue was cleaned, and focused verification passed.

## Evidence

- P001 inventoried the relevant shell CLI surfaces.
- P002/C001 fixed and verified `devicectl hd screenshot` and `devicectl hd file-pull`.
- P003/C004 audited `agentctl` and `cortex` through child checks C002/C003.
- P004/C007 cleaned residual old behavior and verified final contract through child checks C005/C006.
- Final focused tests passed across Cortex and agent-runtime.
- Ledger validation succeeded.

## Criteria Map

- All shell CLI artifact-producing outputs obey Blob contract: satisfied; devicectl artifact commands now return Blob manifests, and no other audited CLI emits raw artifact bytes.
- CLI stdout is small manifest/text instead of raw base64 for screenshot/file-pull: satisfied by fake-service tests.
- Blob namespace is contract-valid: satisfied by `runtime-artifact` upload tests and fixture cleanup.
- Residual old behavior cleaned: satisfied by no `device-screenshot` matches and payload fixture cleanup.
- Work tracked through tickets and checks: satisfied by ledger IDs R001-R008 and C001-C007.

## Execution Map

- R008 summarizes all child outcomes.
- Direct code changes are in shell capability generation and contract tests.

## Stress Test

- The original observed failure class, huge base64 screenshot in shell output, is explicitly tested against.
- File-pull has the same fake-service binary path coverage.
- Agentctl/cortex were separately audited so their lack of wrapping is justified by bounded text/metadata behavior, not assumed.

## Residual Risk

- Full monorepo test suite was not run. Focused verification is strong for this specific CLI Blob contract work.
- Deployment was not done in this package.

## Result IDs

- R008
