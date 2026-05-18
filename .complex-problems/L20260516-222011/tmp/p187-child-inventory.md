# Projection branch inventory and classification

## Problem

Before deleting or preserving any branch, we need a precise inventory of projection-related production and test branches. The risk is hidden residue: old nested wrappers, legacy MCP arrays, duplicate converters, or stale tests may look harmless while still steering future changes.

## Success Criteria

- Search production and tests for projection-related branches, including `display_files`, `_projection`, `tool-output.v1`, `_mcp_content`, `image_url`, `data:image`, `base64`, `llm_content`, nested `result` wrappers, and artifact manifest handling.
- Produce a classification table for suspicious branches: active, test-only, compatibility, or stale.
- Identify exact file/line references for any branch that should be removed in a child problem.
- Avoid changing code in this inventory problem.
