# Devicectl Non-Media Command Coverage Audit

## Problem

Non-media devicectl commands such as shell-exec, mouse, keyboard, clipboard, and file-push should be reachable through shell help/schema and should remain concise terminal JSON receipts.

## Success Criteria

- Inspect devicectl command map and help/schema coverage for non-media commands.
- Verify generated help exposes the intended command family.
- Run focused tests or safe help checks.
- Fix missing or misleading coverage if found.
