# Device/artifact/display boundary verification sweep

## Problem

Run focused verification after Device/artifact/display remediation to prove the final contract holds. This belongs under P708 because screenshots and media paths are high-risk: a small wrong wrapper can reintroduce base64 in context or make display no-op.

## Success Criteria

- Focused scans cover device screenshot, base64, blob URI, display projection, shell output, and tool-output contract terms.
- Relevant tests/lints pass or blockers are recorded with evidence.
- Remaining hits are classified as current contract, test guard, historical archive, or follow-up.
- No active unexamined large-media text leak remains in the swept surfaces.
