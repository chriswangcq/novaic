# P618 Runtime/Cortex Multimodal Compatibility Classification

## Intended Current-Turn Perception

- `image_ref` and `display_perception` paths are intended only for current display-tool perception. Runtime resolves current display image refs to provider-native image content at that boundary.

## Intended History/Text Projection

- Shell/artifact history remains manifest/text.
- Historical display image refs are not resolved back into provider image bytes; tests assert this.

## Risky Residue

- No risky reachable runtime/Cortex compatibility path found that replays historical base64/image bytes into normal LLM history.
