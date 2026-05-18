# Test and migration compatibility residue cleanup

## Problem

Tests, fixtures, migration-like files, and historical compatibility names can keep stale behavior alive by documenting or asserting old missing-generation semantics. These residues must be audited so future work does not reintroduce unsafe defaults.

## Success Criteria

- Inspect inventory hits in tests, fixtures, migration-like files, and compatibility-named code.
- Delete or rewrite tests that assert missing/stale generation success.
- Classify migration-like or historical artifacts as safe only if they are not live runtime behavior.
- Add source guards or tests that prevent reintroducing unsafe compatibility behavior where appropriate.
- Record any intentionally retained historical reference with a clear non-live classification.
