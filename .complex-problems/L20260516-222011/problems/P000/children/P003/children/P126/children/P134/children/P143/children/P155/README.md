# context projection regression test audit

## Problem

The context projection role should be backed by tests that cover message append projections, event read model behavior, and guardrails against historical/raw payload leakage.

This belongs under `P143` because source classification without tests is too easy to regress.

## Success Criteria

- Existing context projection tests are identified.
- Focused tests are run.
- Missing guard coverage is added if source audit finds a real gap.
