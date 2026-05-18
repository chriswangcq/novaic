# Final Residual Risk and Worktree Classification

## Problem

Classify the final local worktree and residual risks so the parent verification does not overclaim external deployment or unrelated dirty state.

## Success Criteria

- Records `git status` and concise diff statistics for the current worktree.
- Classifies changed files owned by this audit versus pre-existing/unrelated dirty state when visible.
- Records residual risk around external repositories/deployment state and whether local verification can or cannot prove it.
- Identifies any remaining untracked or generated artifacts that should be intentionally kept, ignored, or followed up.
