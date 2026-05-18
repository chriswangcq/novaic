# Display Tool Perception Contract Inventory

## Problem

Audit display tool handling to verify image/media outputs are delivered through the intended current-turn perception path and are not stored as raw base64 text in durable tool history or shell-visible output. This belongs under P564 because display is the primary boundary where media should become model-visible without becoming text payload residue.

## Success Criteria

- Records exact scan commands and outputs for display tool implementations, display result adapters, media payload handling, and tests.
- Reads relevant display/perception code/test slices with line references.
- Classifies display outputs as intended current-turn perception, risky history projection, removable compatibility path, or follow-up.
- Identifies whether display returns only bounded textual acknowledgements in normal tool history.
- Captures any high-confidence risky residue for P554 remediation.

