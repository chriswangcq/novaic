# Problem: ContextEvent test and artifact residue classification

## Problem

Repository tests, docs, and ledger artifacts may contain old fallback strings or base64/display examples. These must be classified so they do not masquerade as live code risk.

## Goal

Search tests/docs/problem artifacts for residue patterns and classify them as test coverage, historical ledger artifact, documentation, or live risk.

## Success Criteria

- Non-source hits are classified.
- Test coverage intentionally asserting old failures is distinguished from live residue.
- No non-source hit is left ambiguous.
