# Runtime Shell Handler SDK Wiring

## Problem

Verify active runtime shell/tool handlers instantiate and call the sandbox SDK/service boundary for shell execution.

## Success Criteria

- Records exact scans for sandbox SDK imports/usages in `novaic-agent-runtime`.
- Cites active shell/tool handler source slices.
- Confirms shell execution goes through SDK/service boundary.
- Creates a follow-up if active shell execution bypasses sandboxd.
