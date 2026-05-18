# Audit LLM tool schema and policy payload boundary

## Problem

The LLM-visible tool policy/schema surface must expose shell and explicit payload tools consistently with the payload boundary, without stale direct-tool or hidden large-output assumptions.

This belongs under `P230` because schema/policy is what tells the model which tools exist and how payload inspection is invoked.

## Success Criteria

- Runtime tool surface policy is mapped and confirms payload inspection tools are explicit CLI/shell capabilities where intended.
- Tool schema tests verify payload tools and limits are present and bounded.
- No active schema guidance encourages raw payload/base64 injection into normal context.
