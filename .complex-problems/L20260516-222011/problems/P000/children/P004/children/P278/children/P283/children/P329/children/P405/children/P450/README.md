# Test and fixture compatibility assertion audit

## Problem

Tests and fixtures can accidentally preserve unsafe compatibility semantics by expecting missing/stale generation or legacy active-state behavior to succeed.

## Success Criteria

- Inventory compatibility/generation/legacy hits in tests and fixtures.
- Inspect suspicious assertions around missing/stale generation, fallback, legacy, and active-session behavior.
- Rewrite/delete unsafe assertions if found.
- Classify retained test hits as negative guards or harmless fixtures.
