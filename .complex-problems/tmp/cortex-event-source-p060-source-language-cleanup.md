# Source-of-truth language and artifact cleanup

## Problem

Remove stale docs/comments/test names that describe `context.jsonl`, `steps`, or `summary.md` as the authoritative LLM source. Materialized files may remain only as projection/debug artifacts.

## Success Criteria

- Static scans identify and classify source-of-truth wording.
- Misleading wording is deleted or rewritten.
- Remaining artifact reads are explicitly debug/projection/inspection, not active source semantics.
