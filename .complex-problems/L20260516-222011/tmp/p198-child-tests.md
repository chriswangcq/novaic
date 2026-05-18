# Projection test branch inventory

## Problem

Projection tests may either protect current contracts or accidentally preserve stale compatibility behavior. We need to classify them before test cleanup.

## Success Criteria

- Inventory projection-focused tests across Cortex, runtime, and factory.
- Classify legacy-shape tests as active contract, defensive compatibility guard, test-only fixture, or stale.
- Identify test cleanup/rewrite candidates with exact file/line evidence.
- Do not edit tests in this inventory problem.
