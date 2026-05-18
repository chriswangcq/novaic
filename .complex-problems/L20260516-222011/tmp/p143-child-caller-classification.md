# context.jsonl caller classification

## Problem

All active callers of `context.jsonl` helpers must be classified as debug projection, compatibility path, active source, or stale. Unclassified callers are a source-of-truth ambiguity.

This belongs under `P143` because the project needs a concrete caller map before deciding whether code should stay or be removed.

## Success Criteria

- Repository-wide helper call sites are listed with source pointers.
- Each non-test caller is classified precisely.
- Any stale or unsafe caller is fixed, removed, or split into a follow-up.
