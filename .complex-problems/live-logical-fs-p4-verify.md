# Verify LogicalFS Cutover And Residue Cleanup

## Problem

Prove the implementation is connected, not partial. Run focused tests, broad relevant tests, and residue audits. Any discovered gap must become a follow-up or be fixed before closure.

## Success Criteria

- Focused sandbox/logical-fs tests pass.
- Existing capability/runtime/projection tests touched by this change pass.
- Residue audit checks old symbols, docs, and tests.
- The final result lists remaining platform limitations honestly.
- No old shell execution path remains as a plausible current path.
