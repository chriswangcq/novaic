# LogicalFS Sandbox Blob Call Path Map Check

## Summary

P557 is successful. R552 maps call direction across Cortex, LogicalFS, sandbox, and blob surfaces, and explicitly carries suspicious items forward instead of pretending the map itself is remediation.

## Evidence

- R552.
- P559 R549 / C583: Cortex boundary call path map.
- P560 R550 / C584: sandbox/logicalfs/blob service call path map.
- P561 R551 / C585: artifact/display blob usage map.

## Criteria Map

- Captures import/call scan commands and outputs: satisfied by P559/P560/P561 artifacts.
- Explains current layering direction with file references: satisfied by R552.
- Flags suspicious direct calls for P553: satisfied, `Workspace.materialize()` and `BlobObjectStore`.
- Distinguishes artifact blob usage from RO/RW semantics: satisfied by P561 and R552.

## Execution Map

- Split P557 into Cortex, sandbox/logicalfs, and artifact/blob children.
- Each child recorded scan/source artifacts and a success check.
- R552 rolled the map up and preserved P553 classification items.

## Stress Test

- Hidden-gap stress: suspicious items are named explicitly.
- Over-removal stress: intended artifact/payload blob usage is not marked for deletion.
- Layer confusion stress: sandboxd and LogicalFS roles are separated.

## Residual Risk

No P557 mapping gap remains. P553 must classify/remediate the flagged residue.

## Result IDs

- R552
