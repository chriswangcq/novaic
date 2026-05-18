# Follow-up: Patch active Cortex boundary residue

## Problem
P711 found active Cortex boundary residue but did not patch it. Patch the active candidates and verify the wording no longer collapses Cortex with Sandboxd or foundational file authority.

## Required Work
- Patch `scripts/start.sh:18` to describe Cortex as scope/context/work trace/payload manifest/shell orchestration, not Sandbox ownership.
- Patch `docs/architecture/service-topology.md:29` to distinguish shell orchestration from Sandboxd execution.
- Patch `docs/cortex-architecture.md:31` to distinguish Workspace semantics and shell/sandbox orchestration from foundational file/sandbox ownership.
- Inspect `docs/architecture/service-topology.md:131`; patch only if the contrast remains misleading.
- Re-run focused scans for `Workspace, Sandbox`, `payload manifest/sandbox`, and `Cortex.*Sandbox` over active docs/scripts.
- Run relevant boundary lint if available.

## Success Criteria
- No touched active file still implies Cortex owns Sandboxd process execution or foundational file authority.
- Before/after scan evidence is recorded.
- Relevant boundary lint or targeted verification output is recorded.
- Any remaining intentionally historical contrast is explicitly dispositioned.
