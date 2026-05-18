# Upstream react generation default classification

## Problem

`react_think` and `react_actions` still default `session_generation` to `0`. Determine whether those defaults must be fixed inside P336 for delivery correctness, or whether they are upstream contract work already covered by P337/P339.

## Success Criteria

- Inspect `task_queue/contracts/react_think.py`, `task_queue/contracts/react_actions.py`, and their tests.
- Decide whether changing these defaults is required for P336 parent success.
- If not changed here, record exact follow-on ownership and guard P336 so zero generation still fails before session-ended delivery.
