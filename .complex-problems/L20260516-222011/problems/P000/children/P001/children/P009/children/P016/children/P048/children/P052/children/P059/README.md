# Child Problem: runtime shell wrapper enforces bounded terminal text

## Problem

The runtime shell handler must expose stdout/stderr to the LLM as bounded terminal text. If the subprocess emits large JSON, base64, or other media-like data, the public observation should be truncated or summarized without becoming a semantic media payload.

## Success Criteria

- The active runtime shell wrapper has explicit stdout/stderr length bounds.
- The public shell observation remains terminal-shaped text, including exit code and bounded stdout/stderr.
- Tests or targeted evidence prove large stdout is bounded before entering LLM context.
