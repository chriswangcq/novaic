# Cut Over LLM Factory Docker Runtime to Postgres and Label SQLite Rollback

## Problem

After Postgres backend support and data migration exist, the live `novaic-llm-factory` Docker service must be restarted against Postgres and verified. The old SQLite file must remain as rollback or be archived so it no longer appears to be the current state owner.

This belongs under the LLM Factory migration split because runtime cutover is the production-risk step and needs separate health checks and rollback instructions.

## Success Criteria

- Docker configuration points `llm-factory` at the `novaic_llm_factory` Postgres database using secrets or root-readable config, not world-readable credentials.
- The `novaic-llm-factory` container restarts successfully and `/health` returns ok.
- The running container no longer holds `/opt/novaic/llm-factory/data/llm_factory.db` open.
- Representative reads from the service use data migrated into Postgres.
- The old SQLite DB is retained as a timestamped rollback artifact or renamed/archived with a clear non-current label.
- Rollback instructions are recorded and verified as plausible.
