# Child Problem: runtime test fixtures

## Problem

Runtime tests still mention direct-tool names in finalizer, smoke guardrail, and activity projection fixtures. Some are historical compatibility fixtures, but the intent is not consistently explicit.

## Success Criteria

- Current active-path fixtures use shell-first examples.
- Historical direct-tool fixtures are renamed or commented as legacy archived step data.
- Focused runtime tests pass.
