# Problem: ContextEvent projection and guard verification

## Problem

The most dangerous regression class is tool payloads or image/base64 data leaking back into LLM history/context after the CLI/display contract changes.

## Goal

Re-run focused tests and guards for ContextEvent projection, tool output projection, and workspace payload behavior.

## Success Criteria

- Focused Cortex tests pass.
- Guards show no `stable_json(observation)` fallback or history display expansion path.
- Any leakage candidate is fixed or split into a follow-up.
