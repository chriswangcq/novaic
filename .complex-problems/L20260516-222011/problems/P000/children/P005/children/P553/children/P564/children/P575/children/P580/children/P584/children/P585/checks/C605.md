# P585 Check

## Summary

Success for the scoped design-map ticket. Result `R569` identifies the exact active call path, the byte-leak boundary, the encoded test residue, and a concrete implementation contract for BlobRef-backed display perception. It does not claim the implementation is complete.

## Strict Review

- The runtime display execution boundary is covered: public output, durable payload construction, Blob Service fetch, and small-image inline logic are all mapped with file references.
- The runtime LLM request boundary is covered: step-ref expansion, display-only projection selection, multimodal processing, and provider projection are all mapped.
- The Cortex projection boundary is covered: `read_formatted`, payload parsing, display file conversion, and display-perception formatting are all mapped.
- The stale-test boundary is covered: the current unit test that asserts durable base64 storage is explicitly identified as residue to delete or rewrite.
- The result uses a concrete contract, not a vague recommendation: durable payload stores BlobRef media references, Cortex projects references, runtime resolves only current-round display references.

## Stress Test

Checked the design against the failure mode reported by the user: display should not persist base64 text in Cortex step payloads, but current-round display still must reach the LLM as an image. The design separates durable bytes from perception-time bytes and prevents history replay from injecting old display images.

## Residual Risk

Implementation and regression tests are still pending under the child implementation and verification problems. This check only closes the mapping/design ticket.
