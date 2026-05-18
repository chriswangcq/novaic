# Provider and factory fixture media residue classification

## Problem
Classify media/base64 residue in `novaic-llm-factory` provider adapters and tests as provider-native boundary logic or fixture/redaction proofs. Fix ambiguity if any provider path places media in text content.

## Success Criteria
- OpenAI, Anthropic, and Google/Gemini provider media paths are classified.
- Test fixture base64/data URLs are explicitly redaction/provider-boundary fixtures.
- No provider adapter flattens media into plain text blocks.
