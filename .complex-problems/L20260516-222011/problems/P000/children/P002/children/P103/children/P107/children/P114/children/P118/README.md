# Stable Workspace Path Regression Sweep

## Problem

After schema/help, runtime guard, and docs checks, focused tests must prove the stable path contract remains enforced across the public shell surface.

## Success Criteria

- Run the common shell schema contract tests that cover stable path guidance.
- Run Cortex generated help/schema tests that cover `/cortex/ro` and `/cortex/rw` guidance.
- Run runtime shell guard tests that cover stale backing path rejection.
- If a test gap is discovered, add the smallest regression guard and rerun the focused suite.
