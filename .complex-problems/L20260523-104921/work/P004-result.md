# P004 Result

Removed the remaining Cortex and Entangled server SQLite fallback paths.

Concrete changes:
- Cortex operational storage is Postgres-only; registry initialization now requires the Postgres DSN file and no longer accepts an operational SQLite path or backend selector.
- Cortex tests use an explicit in-memory operational-store fake instead of a temp SQLite database.
- Entangled server-python database creation is Postgres-only; the SQLite Database class, migration CLI, migration planner/executor tests, and SQLite-only support tests were removed.
- Server-python entity/state-transition support code now generates the current Postgres path only instead of carrying SQLite branches.
- Service-side scans for SQLite/fallback tokens across Queue, Gateway, Device, Cortex, Entangled server, Common, Business, startup scripts, and config resources are empty.

Verification:
- Cortex: `python -m py_compile novaic_cortex/operational_store.py novaic_cortex/registry.py novaic_cortex/scope_transition_events.py cortex_tests/workspace_test_utils.py cortex_tests/operational_store_fake.py`
- Cortex: `PYTHONPATH="/Users/wangchaoqun/new-build-novaic/novaic-logicalfs:/Users/wangchaoqun/new-build-novaic/novaic-sandbox-sdk:$PYTHONPATH" pytest tests/test_operational_postgres_store.py tests/test_workspace_registry_dependencies.py tests/test_active_stack_projection.py tests/test_scope_history_api.py tests/test_scope_state.py tests/test_context_event_api_steps_write.py tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_read_source_guards.py tests/test_pr67_wake_child_api.py`
- Entangled server-python: `python -m py_compile packages/server-python/entangled/sql/database.py packages/server-python/entangled/app/config.py packages/server-python/entangled/app/factory.py packages/server-python/entangled/app/state.py packages/server-python/entangled/sql/entity_store.py packages/server-python/entangled/sql/persistence.py packages/server-python/entangled/sql/state_transitions.py packages/server-python/entangled/sql/subagent_state.py packages/server-python/entangled/sql/field_def.py packages/server-python/entangled/sql/entity_def.py packages/server-python/entangled/sql/validation.py packages/server-python/entangled/app/main.py`
- Entangled server-python: `pytest packages/server-python/tests/test_postgres_database_boundary.py packages/server-python/tests/test_postgres_ddl_dialect.py packages/server-python/tests/test_postgres_stream_rowid_queries.py packages/server-python/tests/test_postgres_support_tables.py`
