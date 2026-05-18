# Context read handler residue classification

## Problem

`context_handlers.py` still serves explicit context-read topics. These paths must be classified as safe user/tool inspection paths or stale provider-input fallbacks.

## Success Criteria

- `context_handlers.py` is mapped with line pointers.
- Topic/caller intent for context read is classified.
- Tests covering context-read behavior are identified and run.
- Any stale provider-input use is fixed or split.
