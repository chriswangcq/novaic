# Ticket: audit runtime shell public output bounds

## Problem Definition

The runtime shell wrapper is the first boundary that turns subprocess stdout/stderr into LLM-visible tool output. It must bound terminal text and avoid turning large stdout into unbounded context.

## Proposed Solution

Inspect the active shell handler and wrapper code for stdout/stderr truncation, payload storage, and tool observation shaping. Patch only if active code lacks explicit bounds or leaks raw media-like stdout into public observation text.

## Acceptance Criteria

- Active runtime shell wrapper has explicit public stdout/stderr bounds.
- Large stdout remains terminal-shaped and truncated in public observations.
- Evidence or tests prove runtime shell output is bounded before context projection.

## Verification Plan

Run focused `rg`/file inspection over runtime shell code and execute or add adjacent runtime tests if coverage exists.

## Risks

- Shell must remain useful for normal text output; the contract should bound context without hiding durable full output from RO/payload storage.

## Assumptions

- Cortex projection and broader regression coverage are separate child problems under P052.
