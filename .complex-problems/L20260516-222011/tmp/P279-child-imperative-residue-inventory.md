# Imperative dispatch residue inventory

## Problem

P279 needs a focused inventory of old imperative dispatch, fallback, legacy, compatibility, direct saga creation, direct session mutation, and finalize/session-ended branches before deletion decisions are made. Without a saved inventory, cleanup can become speculative and easy to under- or over-delete.

## Success Criteria

- Saved guard artifact lists searched patterns and matching files.
- Each hit bucket is classified as required boundary, test/docs guard, high-confidence removable residue, or ambiguous follow-up candidate.
- The inventory records enough file references for downstream cleanup children to act without re-discovering the whole surface.
- No production code is changed in this inventory child.
