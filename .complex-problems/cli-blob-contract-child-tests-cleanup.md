# Verify CLI blob contract and clean residual old behavior

## Problem

After CLI repairs, tests and residue scans must prove the active shell CLI paths follow the blob artifact contract and do not silently keep raw base64/media stdout branches alive.

## Success Criteria

- Focused tests cover repaired CLI output contract.
- Existing projection/runtime tests still pass.
- Repository scans find no live raw screenshot/base64 stdout contract in shell CLI paths.
- Any residual compatibility branch is either removed or explicitly justified as test-only/non-live.
