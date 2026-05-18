# Map LogicalFS Sandbox Blob Call Paths

## Problem Definition

P557 must map import/call direction between Cortex, LogicalFS, sandbox, and blob surfaces, distinguishing real-time RO/RW file semantics from artifact blob usage.

## Proposed Solution

Split call-path mapping into Cortex-to-boundary calls, sandbox/logicalfs/blob service calls, and artifact/display blob usage. Each child records scan commands and classifies suspicious direct calls for later residue cleanup.

## Acceptance Criteria

- Import/call scan commands and artifacts exist.
- Current layering direction is explained with file references.
- Suspicious direct calls are flagged for P553.
- Intended blob artifact usage is separated from real-time file semantics.

## Verification Plan

Use targeted `rg` scans for imports, client construction, service URLs, blob refs, `/ro`/`/rw`, materialization vocabulary, and LogicalFS/sandbox names. Read small source slices for high-signal files.

## Risks

- Search terms can miss dynamic imports or env-driven URLs.
- Some direct blob usage is intended.

## Assumptions

- P556 inventory identifies the relevant local roots for this call-path map.
