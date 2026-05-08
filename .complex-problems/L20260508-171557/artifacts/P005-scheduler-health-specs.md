# Scheduler And Health Action Specs

## Problem

Scheduler and health workers still contain bespoke action orchestration and direct effect execution. Convert them to explicit action specs/plans with centralized effect execution.

## Success Criteria

- Scheduler wake scan/dispatch classification is represented by explicit plan/result classification helpers.
- Health recovery action is represented by explicit plan/spec helpers.
- Engines use the generic plan/effect substrate and no longer call direct effect helpers.
- Tests cover scheduler result classifications and health recovery effects.

