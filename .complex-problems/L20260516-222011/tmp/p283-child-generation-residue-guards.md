# Missing or stale generation compatibility residue guard audit

## Problem

Search for compatibility branches, optional generation fallbacks, default generation values, and tests that allow missing/stale generation to succeed. Remove or follow up any residue that weakens the generation boundary.

## Success Criteria

- Source-search optional/missing generation branches across queue session code, outbox workers, saga handlers, tests, and migrations.
- Classify every fallback as required, harmless diagnostic, or dangerous compatibility residue.
- Remove dangerous residue or create a follow-up fix with targeted guard coverage.
- Verify with source guards/tests that attach/finalize paths no longer accept missing/stale generation silently.

