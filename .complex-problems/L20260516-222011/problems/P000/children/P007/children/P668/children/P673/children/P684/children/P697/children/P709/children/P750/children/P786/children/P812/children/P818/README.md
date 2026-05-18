# Child Problem: Wire factory log renderers to safe projection

## Problem

After the projection helper exists, `factory-logs.html` renderers must consistently use it for raw request/response tabs, message bubbles, tool-call arguments, and relevant tool/schema detail rendering.

## Success Criteria

- Raw request and response tabs no longer render unprojected `JSON.stringify` output.
- Message content and reasoning/tool argument displays use projected values.
- Useful metadata remains visible for debugging.
- The visual layout remains readable in the static page.
