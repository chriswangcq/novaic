# Follow-Up: Remove Startup Rebuild Generation Default

## Problem

`queue_service/session_rebuild.py` still reconstructs active session state with:

```python
generation=int(context.get("session_generation") or 1)
```

This silently turns missing identity into a valid generation. The recovery/finalize identity model requires missing or invalid generation to be rejected or skipped, not defaulted.

## Scope

- Update startup session rebuild projection to require explicit positive `session_generation`.
- Skip running saga contexts that lack positive generation.
- Add focused tests around missing, zero, non-numeric, boolean, and valid string/int generation values.
- Keep the change scoped to startup rebuild identity behavior.

## Success Criteria

- No production code under session rebuild defaults missing `session_generation` to `1`.
- Startup rebuild records active session only when the saga context carries positive explicit generation.
- Missing/invalid generation contexts are skipped without fabricating active session state.
- Existing session rebuild boundary/residue tests still pass.
