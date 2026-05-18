# Follow-up: Neutralize internal reply-cap comments from direct im_reply wording

## Problem
Internal comments and boundary rule text still describe reply caps or memory rules using retired direct `im_reply` terminology. This is not active exposure, but it keeps the old tool identity alive in maintenance-facing code.

## Success Criteria
- Internal comments/rule names/messages use “reply action” or “user-visible reply” wording instead of `im_reply` where possible.
- Do not rename persisted counter keys or API endpoints unless clearly safe; this is comment/rule wording cleanup only.
- Focused grep shows remaining `im_reply` hits are executable internal names, explicit legacy compatibility, tests, or historical docs.

## Verification Plan
- Patch comments/rule wording narrowly.
- Run boundary script tests or focused grep if no tests apply.
