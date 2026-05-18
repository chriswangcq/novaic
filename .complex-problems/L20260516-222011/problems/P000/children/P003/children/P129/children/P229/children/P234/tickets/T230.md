# Verify combined large shell/display projection boundary

## Problem Definition

The concrete regression class is large shell output or display image/base64 data appearing as ordinary model-visible history text. This combined audit should prove both large shell and display paths stay compact together.

## Proposed Solution

Reuse code evidence from shell/display/runtime expansion audits, perform a final targeted regression search for raw base64/text injection patterns, and run the combined focused runtime test set that covers shell output contract, no historical image injection, and LLM context expansion.

## Acceptance Criteria

- Shell result projection and display/media projection paths are both mapped to compact/default behavior.
- Evidence shows raw base64/large stdout is not normal history text by default.
- Combined focused tests pass.

## Verification Plan

Search for suspicious base64/raw image injection in runtime context/tool handling tests and code. Run shell output, no historical image injection, and context expansion tests together.

## Risks

- This is a cross-check problem and may duplicate child evidence; keep result focused on combined regression coverage rather than restating all internals.

## Assumptions

- Detailed shell and display internals are already closed in `P237` and `P238`.
