# Child Problem: Display monitor/UI projection boundary inventory

## Problem

Audit monitor/log UI and factory-log rendering paths that show display/tool results to humans, ensuring UI truncation or thumbnails do not imply that raw media bytes are part of the LLM text context.

## Success Criteria

- Records scan commands for monitor, factory logs, and display-related UI rendering.
- Reads relevant UI/log rendering slices with line references.
- Separates human UI preview/truncation from LLM request context.
- Forwards any UI path that stores or displays unredacted raw image bytes as a risky residue.
