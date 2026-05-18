# Scripts and CI Helper Residue Scan Ticket

## Problem Definition

Repository scripts, CI helpers, and shell lint/test scripts may contain stale compatibility, fallback, migration, or policy wording that no longer matches the final runtime/tool contract.

## Proposed Solution

Scan script and CI/helper surfaces, classify residue hits, clean tiny stale wording when safe, and run representative script/lint checks.

## Acceptance Criteria

- Script and CI helper surfaces scanned for residue markers.
- Hits classified.
- Safe stale residue removed.
- Focused verification recorded.

## Verification Plan

- `rg` scans over `.github`, `scripts`, repository shell scripts, and CI/lint helper files.
- Run relevant shell/lint checks or no-code-change verification.
