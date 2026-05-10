# Fix mounted device tools in Runtime tool assembly

## Problem

小马有 Host Desktop device binding and Business can compute mounted `hd_*` tools, but Runtime LLM context assembly only uses Cortex static tool schemas and Runtime execution does not include device executors. As a result, mounted device tools are not visible to the LLM and would not execute even if exposed.

## Success Criteria

- Runtime LLM prepare merges agent-specific mounted device tools from Business into the final tool schemas without polluting Cortex static builtin tools.
- Business `inputSchema` dynamic tool schemas are normalized to LLM assembly's expected `parameters` shape.
- Runtime can execute mounted Host Desktop `hd_*` tools by routing them through Device Service proxy paths.
- Static runtime tools remain stable and legacy/static tests are updated to reflect static-vs-dynamic boundaries.
- Focused tests prove dynamic tool visibility and execution routing.
