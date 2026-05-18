# Attach generation contract inventory

## Problem

Before changing attach code, inventory all active input attach paths and classify whether they require explicit expected wake scope and expected session generation. This belongs under P490 because attach race buffering is legitimate, while no-generation delivery is not.

## Success Criteria

- Runtime attach handler, session outbox publisher, attach effect builder, and session repo attach-race handling are inspected.
- Raw and classified artifacts are saved.
- Any missing or ambiguous attach-generation contract becomes a child/follow-up instead of being waved away.
