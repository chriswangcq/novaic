# Agent Message No Reply Diagnosis

## Problem

The user sent an IM message to the agent, but received no reply and saw no reaction in the agent monitor. Diagnose the concrete cause with production evidence rather than speculation.

## Success Criteria

- Identify the latest relevant user message or notification in production data/logs.
- Trace whether it reached Environment/Entangled, Business subscriber, Queue session dispatch, runtime worker, LLM, and reply publishing.
- Determine the first broken or missing handoff in that chain.
- Provide concrete evidence: timestamps, log lines, database rows, process state, or source behavior.
- If the cause is code/config related, state the minimal fix direction; do not hide uncertainty.
