# Determine root cause and required fix

## Problem

Using the stuck production state, determine whether the failure is code, configuration, operational row state, or frontend projection. If code/config is responsible, identify the active path to patch.

## Success Criteria

- Root cause is mapped to a specific state transition, handler, or service boundary.
- Any code/config change needed is identified with file paths.
- If recovery is sufficient, the operational recovery action is explicit and safe.
