# Finalize producer remaining-stack contract audit

## Problem

Before removing wake finalize fallback stack synthesis, identify every production/test producer of `wake_finalize` context and prove whether it supplies explicit `remaining_stack`. This belongs under P489 because a strict finalizer is only safe if its legitimate producers already meet the contract or can be fixed directly.

## Success Criteria

- All `wake_finalize` context producers are listed with file references.
- Each producer is classified as explicit stack provider, missing provider, or test fixture.
- Missing providers become explicit child/follow-up work instead of preserving fallback.
- Evidence is saved under the ledger tmp directory.
