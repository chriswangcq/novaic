# Migrate LLM Factory Data to Postgres With Row-Count Validation

## Problem

The existing `/opt/novaic/llm-factory/data/llm_factory.db` contains production API keys, model definitions, user keys, and logs. This data must be copied into the dedicated `novaic_llm_factory` Postgres database without losing rows or changing sensitive logging configuration.

This belongs under the LLM Factory migration split because data migration has its own backup, transformation, and verification requirements separate from code support and runtime cutover.

## Success Criteria

- The SQLite database is backed up before migration.
- Pre-migration row counts are recorded for `api_keys`, `models`, `user_keys`, and `llm_logs`.
- Data is imported into Postgres using an idempotent or safely repeatable process.
- Post-migration Postgres row counts match the recorded SQLite counts.
- Sensitive request/response body log fields remain empty/disabled according to current policy.
