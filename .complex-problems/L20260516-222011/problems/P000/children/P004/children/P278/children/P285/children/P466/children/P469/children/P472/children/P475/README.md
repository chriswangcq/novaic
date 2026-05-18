# React saga decision config model

## Problem

Define the smallest explicit config model/provider needed for react saga decisions, covering `max_rounds_before_force_finalize` and `max_stack_hold_retries`.

## Success Criteria

- A clear typed config object or provider exists in an appropriate module.
- Defaults can still come from `ServiceConfig` at a narrow boundary.
- Tests or source structure allow callers to pass explicit values without monkeypatching globals.
