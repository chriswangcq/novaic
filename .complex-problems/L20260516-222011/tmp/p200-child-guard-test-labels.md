# Audit projection guard test labels and assertions

## Problem

Some tests intentionally feed historical or malformed inputs to prove they do not leak images. These should remain, but their names/assertions should read as guardrails, not endorsement of legacy contracts.

## Success Criteria

- Projection guard tests are inspected for misleading legacy naming.
- Any confusing test names or assertions are rewritten.
- Tests that remain clearly express the desired contract.
