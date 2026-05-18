# Runtime Message Assembly And Active Stack Ordering Inventory

## Problem

Audit runtime context/message assembly before provider serialization, including tool-result messages, assistant tool calls, active stack/system injection, and history ordering. This belongs under P574 because raw media text or misplaced system messages can appear before provider adapters even see the request.

## Success Criteria

- Records exact scan commands and outputs for message assembly, context prepare/build functions, active stack insertion, and tool result message construction.
- Reads relevant runtime code/test slices with line references.
- Classifies tool-result/history/system-message projections as intended, risky, removable, or follow-up.
- Identifies whether active stack ordering can interfere with current-turn display/image delivery.
- Captures any high-confidence risky residue for P554 remediation.

