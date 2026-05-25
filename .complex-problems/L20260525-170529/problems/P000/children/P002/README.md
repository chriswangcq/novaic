# Render Agent Monitor titles from public fields, not reasoning keywords

## Problem

The frontend `ActivityTimeline` currently derives public titles from `record.text` for reasoning records. This creates incorrect labels such as `正在组织回复` from private thought content. The app should consume structured `public_title` when available and use safe structured fallback for legacy records.

## Success Criteria

- TypeScript activity record type includes `public_title`.
- `useActivityTimeline` normalization carries only the explicit public title field, without spreading raw entities.
- `ActivityTimeline` uses `public_title` first, then existing structured tool/phase fallback.
- Reasoning text is still shown as detail when safe, but is not used to infer titles.
- Frontend tests cover legacy records, explicit public titles, read/reply behavior, and the screenshot regression.
