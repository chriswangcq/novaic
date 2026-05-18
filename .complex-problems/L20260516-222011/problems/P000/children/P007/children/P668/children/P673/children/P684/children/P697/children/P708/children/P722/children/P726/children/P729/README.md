# Runtime artifact manifest handling discovery

## Problem

Discover how Runtime parses shell `tool-output.v1` artifact manifests, stores durable payload/raw data, and exposes LLM-visible bounded content for shell results.

## Success Criteria

- Runtime parser/handler for shell `tool-output.v1` manifests is identified with file pointers.
- Durable raw payload versus public LLM-visible content separation is identified.
- Tests proving bounded public shell text and durable raw payload behavior are identified or gaps recorded.
- Any active Runtime path that injects raw media/base64 into public tool content is listed.
