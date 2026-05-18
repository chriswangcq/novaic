# Aggressive projection stale-branch regression sweep

## Problem Definition

After production and test cleanup, remaining projection code must be aggressively swept for unclassified branches, stale references, and provider-side conversion gaps. The known Google/Gemini multimodal conversion gap must not be hidden by passing OpenAI/Anthropic tests.

## Proposed Solution

Split into a final static projection audit, Google/Gemini multimodal provider fix/coverage, and final focused regression chain. Treat any suspicious branch or test failure as a blocking child/follow-up rather than a note.

## Acceptance Criteria

- Projection keyword `rg` audit has no unclassified suspicious branch.
- Google/Gemini multimodal conversion is covered and fixed if currently broken.
- Focused Cortex/runtime/factory projection test chain passes.
- Residual risks and intentional compatibility branches are explicitly stated.

## Verification Plan

Run targeted static searches, inspect provider conversion paths, add/fix provider tests, and run the full focused projection test chain.

## Risks

- Google/Gemini payload shape may need careful provider-specific conversion.
- Static search may surface unrelated old docs; classify docs separately from active code.

## Assumptions

- Provider multimodal conversion belongs in this final regression sweep because it was found by projection inventory and can silently break display perception for non-OpenAI providers.
