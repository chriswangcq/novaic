# React saga config tests

## Problem

Add and run focused tests proving react saga decisions are controlled by explicit config, not global `ServiceConfig` monkeypatching.

## Success Criteria

- Tests cover non-default round cap for `react_actions`.
- Tests cover non-default round cap or stack-hold retry limit for `react_think`.
- A guard proves decision adapter functions no longer directly reference `ServiceConfig.MAX_ROUNDS_BEFORE_FORCE_FINALIZE`.
- Test logs are saved under `.complex-problems/L20260516-222011/tmp/p477/`.
