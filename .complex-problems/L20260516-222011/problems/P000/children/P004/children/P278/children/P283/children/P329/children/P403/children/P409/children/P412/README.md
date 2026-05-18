# React contract residue classification

## Problem

`react_think.py` and `react_actions.py` contain round, stack-depth, retry, and session-generation related guard hits. They must be classified or patched so React contract defaults cannot weaken live session generation boundaries.

## Success Criteria

- Inspect React contract guard hits from P402.
- Confirm `session_generation` is explicit and validated, not defaulted.
- Classify round/retry/stack-depth defaults as non-session control counters or patch if unsafe.
- Run focused React contract tests.
