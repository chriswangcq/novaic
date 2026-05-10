# Phase 5D.2 Guard Coverage Review And Tightening

## Problem

Review whether the cleanup is protected by durable tests or static guards. If a removed authority path can be reintroduced without any test/static check failing, add the smallest appropriate guard.

This belongs under P048 because cleanup without guard coverage can regress silently in later AI-generated changes.

## Success Criteria

- Inspect existing tests/static checks around scope projection, active stack, step formatting projection, payload manifest, and scope lock fail-closed behavior.
- Identify at least one concrete guard per high-risk removed path, or add a small test/static guard when missing.
- Run the new or affected guard tests.
- Record any intentionally unguarded historical-only terms with rationale.
