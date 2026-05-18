# Ticket: Classify ContextEvent non-source residue

## Goal

Search non-live-code surfaces for ContextEvent lifecycle residue patterns and classify them so historical/test evidence is not confused with live risk.

## Acceptance Criteria

- Tests, docs, and ledger artifacts are searched for relevant residue patterns.
- Hits are classified as regression coverage, documentation/history, ledger artifact, or live risk.
- No ambiguous non-source residue remains.
