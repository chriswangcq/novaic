# Finalize restart atomicity implementation

## Problem

Implement the designed transaction-boundary change in session repository code without touching unrelated paths.

## Success Criteria

- Finalize-with-pending records restart transition and outbox inside the same global transaction as accepted finalize.
- No after-transaction restart recording remains for this path.
- Syntax/source guard passes.
