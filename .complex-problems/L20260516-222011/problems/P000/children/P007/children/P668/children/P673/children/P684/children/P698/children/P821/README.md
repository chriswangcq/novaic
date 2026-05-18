# LLM factory launch status audit

## Problem

`novaic-llm-factory` has its own `main.py` (port 9100) and `factory/app.py` but is absent from all three launch scripts. It appears to be an orphaned service entrypoint.

## Success Criteria

- llm-factory launch status is classified: should it be in start.sh, or is it intentionally standalone/manual-only?
- If it should be orchestrated, a follow-up is recorded. If standalone is intentional, this is documented.
- No stale references to llm-factory in launch scripts.
