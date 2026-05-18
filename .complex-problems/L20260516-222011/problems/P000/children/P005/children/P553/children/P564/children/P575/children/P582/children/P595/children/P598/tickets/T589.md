# Ticket: Inventory Display Handler Durable ImageRef Tests

## Problem Definition

The runtime display handler must persist display media as BlobRef `image_ref`/display metadata and keep public chat text bounded, without copying inline image data into durable payloads.

## Proposed Solution

Scan display handler tests around `_exec_display`, `_ok`, durable payload generation, `image_ref`, and no-`data` assertions. Run focused tests that protect inline-image and BlobRef display durable paths.

## Acceptance Criteria

- Exact scan and test commands are recorded.
- Tests proving display public output uses placeholders without inline data are cited.
- Tests proving durable payload stores `image_ref` and `display_files` BlobRef metadata are cited.
- Tests proving durable payload does not depend on inline image bytes are cited.
- Any missing coverage is recorded as a follow-up.

## Verification Plan

Run focused display handler tests in `test_tool_handlers_display_chat_history.py` and related no-historical projection tests if needed.

## Risks

- Some tests intentionally use inline image data to verify public-output redaction; the result must distinguish input fixtures from durable output.

## Assumptions

- BlobRef display is the durable contract; current display perception may resolve BlobRefs later at runtime, outside the display handler.
