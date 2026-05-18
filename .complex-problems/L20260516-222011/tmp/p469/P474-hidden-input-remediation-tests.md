# Hidden input remediation tests and guards

## Problem

Prove the hidden-input remediation is not just code movement. Focused tests/guards must show saga decisions can be controlled through explicit config and that no direct decision-path `ServiceConfig` read remains.

## Success Criteria

- Add or update focused tests for injected round/stack limits in `react_think` and `react_actions`.
- Run relevant existing tests for session FSM, react saga routing, and hidden-input/residue guards.
- Save test logs under `.complex-problems/L20260516-222011/tmp/p474/`.
- Record any remaining risk explicitly.
