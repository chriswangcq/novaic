# Verify and recover production IM session state

## Problem

The affected production message must be accounted for after the Redis/disk incident and manual replay. We need evidence that the notification was processed, an agent reply was written, the session returned to `no_active`, and Redis/disk are healthy.

## Success Criteria

- The affected notification is `processed`.
- A corresponding agent reply exists in `environment_im_messages`.
- The queue session state for the affected agent/subagent is `no_active`.
- Redis persistence and disk usage are healthy.

