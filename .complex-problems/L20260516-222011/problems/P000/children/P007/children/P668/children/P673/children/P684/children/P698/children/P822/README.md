# Blob service and Sandboxd dual entrypoint audit

## Problem

Both `novaic-blob-service` and `novaic-sandbox-service` have two entrypoint files each: a `main_*.py` wrapper at the repo root level and an internal `*/main.py`. Need to verify the wrapper pattern is intentional (thin launcher delegating to internal app) rather than a stale duplicate.

## Success Criteria

- Each dual-entrypoint pair is classified: wrapper pattern (keep both) or duplicate (remove one).
- If wrapper pattern, the relationship is clear (wrapper imports internal).
- No stale or divergent launch logic between the two files.
