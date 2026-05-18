# Cortex Shell Fallback And Executor Bypass Classification

## Problem

Classify Cortex occurrences of local shell fallback, process-runner bypass, direct subprocess execution, and sandbox executor compatibility that could bypass sandboxd. This belongs under P562 because shell must go through `MountNamespaceLogicalFS` and sandboxd.

## Success Criteria

- Records exact Cortex scan commands and outputs for fallback/process/subprocess/sandbox executor terms.
- Reads relevant code slices with line references.
- Confirms whether any production local execution fallback remains.
- Identifies any remediation candidate for P554.
