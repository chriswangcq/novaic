# VmControl HD screenshot contract comment cleanup

## Problem
VmControl HD tools Rust code contains stale screenshot-to-LLM comments that conflict with the current blob/display/tool-output contract.

## Success Criteria
- HD tools comments describe screenshot capture/storage/display through blob/display contract, not direct LLM base64/image injection.
- No stale screenshot-to-LLM wording remains in the relevant Rust route code.
- Rust formatting/check or targeted scan runs if available.
