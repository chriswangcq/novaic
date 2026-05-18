# Cortex focused compatibility behavior tests

## Problem

Run the focused Cortex behavior tests that prove context event lifecycle, projection, payload inspection, shell blob contract, legacy lifecycle removal, and compatibility boundary guards behave as designed.

## Success Criteria

- Run focused `novaic-cortex` tests for context event lifecycle/skill lifecycle/steps/context writes, payload inspection, read-source guards, projection/store, scope summary, shell blob contract, tool/step output projection, legacy lifecycle removal, and lock/compat guards.
- Save the exact command, exit status, and log under `.complex-problems/L20260516-222011/tmp/p457/`.
- If tests fail, create a repair follow-up with failing test names and first actionable traceback.
