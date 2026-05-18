# Child Problem: runtime guard and smoke assertions

## Problem

Runtime guard tests mention old direct tools in negative assertions and comments. These should be explicit denylist/removed-tool assertions, not normal examples.

## Success Criteria

- Guard assertions keep old names only as negative checks.
- Comments do not imply old names are current reply/observe paths.
- Focused guard tests pass.
