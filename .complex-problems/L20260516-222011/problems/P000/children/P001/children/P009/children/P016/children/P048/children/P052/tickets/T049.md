# Ticket: audit and enforce terminal-shaped shell observations

## Problem Definition

The shell tool should look like terminal output in LLM context: bounded stdout/stderr text plus file-change hints, not a transport for binary/media payloads. Previous failures showed screenshot/base64 data entering tool context through shell output, so the active shell projection contract needs a focused audit and test coverage.

## Proposed Solution

- Inspect shell observation wrapping/projection paths in runtime and Cortex.
- Confirm active shell output truncation and payload-pointer behavior.
- Patch active code if shell can still inject large media/base64 as unbounded semantic context.
- Add or update focused tests that simulate large stdout/base64-like output and assert bounded terminal-shaped context.

## Acceptance Criteria

- Shell observations exposed to LLM context are bounded text, not raw binary/media payloads.
- The contract points complete data to Cortex RO step/payload records or artifact manifests rather than inline context.
- Focused tests or scans prove a large-media stdout case is bounded and does not become model-visible image/base64 semantics.

## Verification Plan

- Run targeted `rg` scans over shell handler/projection code for truncation, payload references, and base64/media handling.
- Run focused runtime/Cortex tests covering shell output projection and no historical tool image injection.
- Add a regression test if existing coverage does not directly simulate oversized stdout.

## Risks

- Shell is intentionally general-purpose; it may legitimately print long text. The fix should bound and preserve terminal semantics without blocking normal text inspection.

## Assumptions

- Complete shell output can remain available through durable step payloads/RO files; the LLM-facing observation does not need to inline everything.
