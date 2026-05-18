# Frontend Timeline Preview Truncation and Escaping

## Problem

Audit the Agent Monitor timeline/list preview rendering path to ensure tool outputs shown inline are escaped, bounded, and summarized, rather than rendering raw large tool result text such as base64 screenshots.

## Success Criteria

- Records exact scans for timeline/list preview components and helper functions.
- Cites frontend slices showing escaping, truncation, or preview-only rendering.
- Runs focused tests if available, or records missing test coverage as a gap.
- Creates a follow-up if inline timeline preview can render raw unbounded image/base64 text.
