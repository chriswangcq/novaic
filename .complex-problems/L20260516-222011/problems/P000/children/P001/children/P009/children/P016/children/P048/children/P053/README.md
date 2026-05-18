# Child Problem: base64 leakage regression guards

## Problem

Once CLI, shell, and display projection contracts are fixed, the repo needs regression guards so future media tools cannot accidentally reintroduce raw base64 into shell text, Cortex context, or LLM request messages.

## Success Criteria

- A focused scan or test catches obvious image-base64 leakage patterns in active media/display/shell output paths.
- Legitimate tiny fixtures or historical examples are explicitly named/classified so the guard does not become noisy.
- The guard is included in a relevant existing test or CI path rather than existing only as an ad hoc manual command.
