# Problem: Cortex direct scope-end contract cleanup

## Problem

Direct scope-end/archive diagnostics may bypass the intended lifecycle ownership contract or omit structured reason/generation/remaining-stack information.

## Goal

Inspect and clean direct scope-end API behavior so it is explicit, structured, and not confused with ContextEvent projection.

## Success Criteria

- Direct scope-end behavior is explicit.
- Missing structured diagnostics are fixed or documented as not applicable.
- Regression tests or guards cover the contract.
