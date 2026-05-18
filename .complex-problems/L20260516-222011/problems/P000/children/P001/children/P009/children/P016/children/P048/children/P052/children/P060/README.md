# Child Problem: Cortex shell step projection preserves terminal semantics

## Problem

Even if runtime shell output is bounded, Cortex step/context projection can accidentally rehydrate durable payloads or historical shell outputs into large text. The Cortex projection layer must keep shell observations terminal-shaped and pointer-oriented.

## Success Criteria

- Cortex projection does not re-inline full durable shell payloads into LLM history.
- Historical shell steps are represented as bounded terminal text or pointers.
- Focused tests or scans cover the shell step projection path.
