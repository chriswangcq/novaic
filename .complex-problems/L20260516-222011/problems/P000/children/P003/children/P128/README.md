# Agent runtime context client and history expansion audit

## Problem

Agent runtime prepares LLM calls by reading Cortex step/context data and expanding `step_ref` results. This layer can accidentally defeat Cortex payload externalization by loading formatted results into history incorrectly or by mishandling current versus historical display calls.

## Success Criteria

- Runtime context preparation and step result client code paths are mapped with concrete file/function pointers.
- The runtime distinguishes current-round display/media projection from historical manifest-only replay.
- Runtime does not expand shell/payload/blob bytes beyond bounded terminal text and durable references.
- Active skill stack/system-message insertion is checked so it does not suppress or reorder current-round media projection.
- Targeted runtime tests prove no historical image/base64 injection and correct current-round image availability.
