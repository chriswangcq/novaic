# Active Stack and System Message Display Ordering Test Coverage

## Problem

Verify that tests protect the ordering contract where active-stack/system messages do not prevent the immediately preceding current-round `display` tool result from being projected as `display_perception`.

## Success Criteria

- Records exact scans for active-stack, system-message, latest tool-call, and current-round projection tests.
- Cites tests proving current display perception still works when active-stack/system messages are appended after tool output.
- Cites tests proving non-current display messages fall back to history projection.
- Creates a concrete follow-up if ordering coverage is missing or indirect.
- Explains why this belongs under the display regression inventory split.
