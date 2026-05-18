# Service code semantic residue discovery

## Problem

Audit service code for comments, constants, route names, wrappers, or compatibility remnants that imply wrong ownership between Cortex, Gateway, Business, Device/devicectl, Queue, Runtime, Blob, LogicalFS, Sandboxd, shell, display, VMuse, and VmControl.

## Success Criteria

- Focused scans cover service source directories and tests without bulk-loading large generated files.
- Findings classify active stale code/comments versus intentional protocol code, auth encoders, tests, or fixtures.
- Exact safe code remediation candidates are listed.
- No code is modified in this discovery child.
