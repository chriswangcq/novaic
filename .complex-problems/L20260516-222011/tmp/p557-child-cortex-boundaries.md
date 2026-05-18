# Cortex Boundary Call Path Map

## Problem

Map how Cortex calls or references LogicalFS, sandbox, and blob-related surfaces. This child belongs under P557 because Cortex is the top semantic layer and should not own low-level real-time filesystem mechanics directly.

## Success Criteria

- Scans Cortex imports/calls for LogicalFS, sandbox, blob, RO/RW, materialization, and artifact terms.
- Reads high-signal Cortex files in bounded slices.
- Classifies current call direction and suspicious direct paths.
- Records exact commands and artifacts.
