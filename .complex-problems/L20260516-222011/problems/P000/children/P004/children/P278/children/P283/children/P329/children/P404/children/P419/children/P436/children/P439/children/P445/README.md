# Cortex context endpoint and test cleanup

## Problem

Cortex context projection endpoints and tests should retain only explicit materialized projection behavior. Any compatibility wording, stale DFS/LLM-history implication, or dead context batch path should be cleaned.

## Success Criteria

- `/v1/context/read|append|batch` endpoint docs/comments/tests use explicit materialized projection language.
- Dead compatibility tests or stale names are removed or renamed.
- Cortex context event API tests pass.
- Prepare-path guards still pass.
