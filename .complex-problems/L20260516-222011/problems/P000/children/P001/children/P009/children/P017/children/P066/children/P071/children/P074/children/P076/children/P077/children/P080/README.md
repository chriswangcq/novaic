# Classify Business environment IM endpoints as current shell boundary

## Problem
`business/internal/environment.py` still exposes `environment_im_read` and `environment_im_reply`. These names match old direct-tool concepts, but may now be the current shell `agentctl` boundary. The boundary needs explicit classification and non-misleading wording.

## Success Criteria
- Environment IM endpoints are confirmed current or removed if obsolete.
- Comments/docstrings/API names do not imply direct LLM tools.
- Any required current shell boundary tests still pass.
