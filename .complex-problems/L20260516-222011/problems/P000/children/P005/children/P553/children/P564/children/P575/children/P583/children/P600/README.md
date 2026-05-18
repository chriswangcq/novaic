# Factory Log Request Context and Raw JSON Boundary

## Problem

Audit factory-log storage/API and raw JSON detail paths to ensure they represent actual LLM request context, not monitor previews, and do not store unredacted display raw media bytes outside the intended provider request.

## Success Criteria

- Records exact scans for factory-log APIs, request/response body persistence, and raw JSON rendering data.
- Cites backend slices that show what is stored for LLM calls.
- Cites frontend slices that show raw JSON detail is a human debug view of stored call records.
- Creates a follow-up if raw media bytes are stored in factory logs unexpectedly.
