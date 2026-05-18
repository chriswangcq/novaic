# Cortex projection branch inventory

## Problem

Cortex is responsible for parsing step/tool result payloads and producing history/display projections. We need to classify Cortex projection branches before any stale cleanup.

## Success Criteria

- Inventory `novaic-cortex/novaic_cortex/step_result_projection.py` and related API projection call sites.
- Classify suspicious Cortex branches involving `tool-output.v1`, `llm_content`, `_mcp_content`, display files, data URLs, artifact manifests, and truncation.
- Identify stale Cortex cleanup candidates with exact file/line evidence.
- Do not edit code in this inventory problem.
