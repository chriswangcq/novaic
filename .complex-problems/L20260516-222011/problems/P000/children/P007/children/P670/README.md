# Smoke-test ergonomics and deployment freshness guard audit

## Problem

Inspect smoke-test scripts, deployment freshness guards, runbooks, and tests used after deploy/runtime changes. Find places where smoke failures are hard to interpret, rely on stale tool contracts, or omit important runtime checks.

## Success Criteria

- Existing smoke scripts, deploy freshness guards, and smoke-related docs/tests are searched and inspected.
- Current expected smoke behavior is documented or encoded where missing.
- Low-risk script/test/doc improvements are applied for concrete gaps.
- Smoke-related checks are run locally where possible without destructive deployment actions.
