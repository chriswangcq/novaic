# Classify remaining projection compatibility branches

## Problem

Projection cleanup is only complete if remaining branchy code is intentional and documented. Search for removed stale symbols and inspect remaining projection markers so no old inactive branch remains by accident.

## Success Criteria

- Removed stale symbol `resolve_for_llm` is absent from active source/tests.
- Remaining projection-related branches are listed and classified as intentional or follow-up-worthy.
- Any unclassified stale branch creates follow-up work.
