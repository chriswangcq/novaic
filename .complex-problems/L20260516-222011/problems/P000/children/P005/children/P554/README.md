# LogicalFS Sandbox Blob Layering Remediation

## Problem

Remove or tighten high-confidence stale fallback/backdoor paths found by the residue inventory. This child belongs under P005 because the user explicitly prefers physical cleanup over compatibility residue.

## Success Criteria

- High-confidence stale paths are removed or replaced with intended service boundaries.
- Ambiguous paths are not guessed; they are documented or split into follow-up problems.
- Changed code has focused tests or static guards.
- No local fallback is retained unless explicitly justified.
