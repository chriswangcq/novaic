# Sandbox SDK Runtime Boundary Test Coverage

## Problem

Verify focused tests cover the SDK/service execution boundary and shell output contract after the artifact/blob/shell refactor.

## Success Criteria

- Runs focused SDK tests if present.
- Runs focused runtime shell output/tool handler tests.
- Records exact commands and outputs.
- Classifies missing tests as acceptable, risky, or follow-up.
- Creates a follow-up if tests do not cover the active SDK/runtime boundary.
