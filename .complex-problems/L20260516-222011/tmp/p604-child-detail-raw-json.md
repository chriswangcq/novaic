# Frontend Detail Modal and Raw JSON Boundary

## Problem

Audit the Agent Monitor detail/modal/raw JSON surfaces to distinguish intentional raw inspection views from normal timeline previews, and ensure raw/detail rendering is escaped, bounded, and not confused with LLM request context.

## Success Criteria

- Records exact scans for detail modal, raw JSON tab, request/response body rendering, and bounds.
- Cites frontend slices showing HTML escaping, JSON stringification boundaries, or size limits.
- Separates inspect/debug raw views from normal user-facing timeline preview behavior.
- Creates a follow-up if raw/detail views can inject unescaped HTML or unbounded raw image/base64 text.
