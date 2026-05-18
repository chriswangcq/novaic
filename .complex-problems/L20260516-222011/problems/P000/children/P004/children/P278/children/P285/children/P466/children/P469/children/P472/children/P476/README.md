# React saga config wiring

## Problem

Wire the explicit config model into `react_think.py` and `react_actions.py` so their decision adapter functions do not directly reference `ServiceConfig`.

## Success Criteria

- `react_think._decide_and_build_actions` uses explicit config input/provider values.
- `react_actions._decide_finalize_or_continue` uses explicit config input/provider values.
- Existing saga registration and callback signatures continue to work.
- No new compatibility branch or hidden fallback is introduced.
