# Audit Cortex Shell Step and Payload Persistence Boundary

## Problem Definition

P615 must verify shell results are recorded in Cortex as step/payload data with payload refs and bounded previews, so full output is recoverable from RO/payload files without stuffing raw full output into normal LLM history.

## Proposed Solution

Scan Cortex step write/read/projection paths for payload refs, preview/head/tail, payload storage, and step index behavior. Cite code/test slices and run focused Cortex tests for context event step writes, read model, runtime truncation, and step index artifacts.

## Acceptance Criteria

- Cortex persistence scan and slices are recorded.
- Evidence shows full/big output is represented by payload refs or payload files with bounded preview in normal context.
- Focused Cortex persistence/projection tests pass.
- Risky durable inline shell media/raw bytes are forwarded as follow-up if found.

## Verification Plan

Run focused Cortex tests around context event API step writes, context event read model, runtime tool output truncation, and step index outcome if available.

## Risks

- Cortex has multiple projection paths; scan must avoid checking only the newest path.

## Assumptions

- Durable payload files may contain complete output; the issue is whether normal LLM history receives bounded refs/previews instead of complete raw bytes.
