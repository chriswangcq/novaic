# Scan direct session SQL table access

## Problem

Find direct SQL/table access for session state, active session, inbox, and outbox tables. Classify whether matches are legitimate repository/adapter code, tests, docs, or risky active paths outside the intended boundary.

## Success Criteria

- Search patterns and representative matches are recorded.
- Production matches are classified by owner module and boundary legitimacy.
- Any direct production SQL outside the intended repository/ledger/outbox adapter boundary is flagged for cleanup.
