# Map workspace context.jsonl helper behavior

## Problem Definition

The workspace `context.jsonl` helper methods need a precise implementation map so later caller audits can classify them correctly and avoid treating them as hidden LLM context authority.

## Proposed Solution

Inspect the five helper methods in `workspace.py`, classify whether each reads, appends raw messages, or appends already-projected messages, and note any raw payload risk.

## Acceptance Criteria

- All five helpers have source pointers.
- Each helper has a role classification.
- Raw payload persistence risk is identified or ruled out from helper behavior.

## Verification Plan

Use `nl` and `rg` to map helper definitions. Run no code changes unless the implementation itself contains an obvious local bug.

## Risks

- Helper names may imply authority even if actual active callers do not use them that way.

## Assumptions

- Caller and prepare-path authority questions are handled by sibling problems.
