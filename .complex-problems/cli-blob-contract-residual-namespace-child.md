# Clean stale CLI artifact Blob namespace fixtures

## Problem

Some tests/examples still use pre-contract artifact namespaces such as `device-screenshot`. These residues can mislead future CLI implementations even if live code is fixed.

## Success Criteria

- Runtime-generated artifact fixtures use `blob://runtime-artifact/...`.
- No `device-screenshot` namespace remains in CLI/tool-output contract tests.
- Changes are limited to contract-relevant fixtures and do not rewrite unrelated storage tests.
- Relevant projection and tool-output tests pass.
