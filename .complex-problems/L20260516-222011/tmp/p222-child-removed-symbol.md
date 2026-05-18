# Prove removed projection symbols are absent

## Problem

The stale `resolve_for_llm` branch was deleted earlier. Confirm it is absent from active source and tests, separating active code from ledger/history references.

## Success Criteria

- Active package source/tests have no `resolve_for_llm` references.
- Any remaining matches are ledger/history/documentation only and are classified as non-runtime.
