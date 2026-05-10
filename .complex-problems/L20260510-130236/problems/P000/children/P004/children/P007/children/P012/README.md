# Prove Blob Boundary Guardrail Behavior

## Problem

A guardrail that merely passes the current tree may still be useless if it cannot catch an obvious bypass. The repo needs evidence that the new guardrail permits allowed paths and rejects direct live `RO` / `RW` bypass shapes.

This child belongs under T006 because it closes the guardrail with positive and negative proof.

## Success Criteria

- Targeted tests pass in the current tree.
- A synthetic negative case or fixture proves obvious direct `/v1/objects`, `BlobCortexStore`, or forbidden `CortexStore` live authority usage is rejected.
- The result records the exact commands and outcomes.
