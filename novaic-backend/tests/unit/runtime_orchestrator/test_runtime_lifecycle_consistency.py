import tempfile
from concurrent.futures import ThreadPoolExecutor

from runtime_orchestrator.db import close_database, get_db, init_database
from runtime_orchestrator.db.repositories.runtime import RuntimeRepository
from runtime_orchestrator.db.schema import init_runtime_schema_sync


def _insert_agent_and_subagent(agent_id: str, subagent_id: str) -> None:
    db = get_db()
    db.execute(
        """
        INSERT INTO agents (id, name, created_at)
        VALUES (?, ?, datetime('now'))
        """,
        (agent_id, "test-agent"),
    )
    db.execute(
        """
        INSERT INTO subagents (subagent_id, agent_id, type, status, created_at, updated_at)
        VALUES (?, ?, 'main', 'sleeping', datetime('now'), datetime('now'))
        """,
        (subagent_id, agent_id),
    )
    db.commit()


def test_get_or_create_active_runtime_is_idempotent_for_retries():
    close_database()
    with tempfile.TemporaryDirectory() as tmp_dir:
        init_database(
            data_dir=tmp_dir,
            db_file="runtime_lifecycle_test.db",
            init_schema_func=init_runtime_schema_sync,
        )
        try:
            agent_id = "agent-life-1"
            subagent_id = "main-agent-li"
            _insert_agent_and_subagent(agent_id, subagent_id)
            repo = RuntimeRepository(get_db())

            runtime1, created1 = repo.get_or_create_active_runtime(subagent_id, agent_id, [])
            runtime2, created2 = repo.get_or_create_active_runtime(subagent_id, agent_id, [])

            assert created1 is True
            assert created2 is False
            assert runtime1.runtime_id == runtime2.runtime_id
            assert repo.has_active_runtime(subagent_id, agent_id) is True
        finally:
            close_database()


def test_repeated_stop_transition_keeps_state_consistent():
    close_database()
    with tempfile.TemporaryDirectory() as tmp_dir:
        init_database(
            data_dir=tmp_dir,
            db_file="runtime_lifecycle_test.db",
            init_schema_func=init_runtime_schema_sync,
        )
        try:
            agent_id = "agent-life-2"
            subagent_id = "main-agent-li"
            _insert_agent_and_subagent(agent_id, subagent_id)
            repo = RuntimeRepository(get_db())
            runtime = repo.create_runtime(subagent_id, agent_id, [])

            first = repo.cas_set_status(runtime.runtime_id, ["active"], "completed")
            second = repo.cas_set_status(runtime.runtime_id, ["active"], "completed")
            final_runtime = repo.get_by_id(runtime.runtime_id)

            assert first is True
            assert second is False
            assert final_runtime is not None
            assert final_runtime.status == "completed"
        finally:
            close_database()


def test_active_runtime_listing_is_deterministic_when_timestamps_tie():
    close_database()
    with tempfile.TemporaryDirectory() as tmp_dir:
        init_database(
            data_dir=tmp_dir,
            db_file="runtime_lifecycle_test.db",
            init_schema_func=init_runtime_schema_sync,
        )
        try:
            agent_id = "agent-life-3"
            subagent_id = "main-agent-li"
            _insert_agent_and_subagent(agent_id, subagent_id)
            repo = RuntimeRepository(get_db())
            db = get_db()
            created_at = "2026-02-19T00:00:00"

            db.execute(
                """
                INSERT INTO agent_runtimes (
                    runtime_id, subagent_id, agent_id, current_round_id, current_round_num,
                    phase, context, pending_actions, status, created_at, updated_at
                ) VALUES (?, ?, ?, 'round-1', 1, 'need_think', '[]', '[]', 'active', ?, ?)
                """,
                ("rt-bbb", subagent_id, agent_id, created_at, created_at),
            )
            db.execute(
                """
                INSERT INTO agent_runtimes (
                    runtime_id, subagent_id, agent_id, current_round_id, current_round_num,
                    phase, context, pending_actions, status, created_at, updated_at
                ) VALUES (?, ?, ?, 'round-1', 1, 'need_think', '[]', '[]', 'active', ?, ?)
                """,
                ("rt-aaa", subagent_id, agent_id, created_at, created_at),
            )
            db.commit()

            runtimes = repo.get_all_active_runtimes()
            runtime_ids = [runtime.runtime_id for runtime in runtimes]

            assert runtime_ids[:2] == ["rt-aaa", "rt-bbb"]
        finally:
            close_database()


def test_concurrent_get_or_create_returns_single_active_runtime():
    close_database()
    with tempfile.TemporaryDirectory() as tmp_dir:
        init_database(
            data_dir=tmp_dir,
            db_file="runtime_lifecycle_test.db",
            init_schema_func=init_runtime_schema_sync,
        )
        try:
            agent_id = "agent-life-4"
            subagent_id = "main-agent-li"
            _insert_agent_and_subagent(agent_id, subagent_id)

            def _worker():
                repo = RuntimeRepository(get_db())
                runtime, _ = repo.get_or_create_active_runtime(subagent_id, agent_id, [])
                return runtime.runtime_id

            with ThreadPoolExecutor(max_workers=8) as pool:
                runtime_ids = list(pool.map(lambda _: _worker(), range(8)))

            assert len(set(runtime_ids)) == 1
        finally:
            close_database()


def test_concurrent_status_cas_allows_single_winner():
    close_database()
    with tempfile.TemporaryDirectory() as tmp_dir:
        init_database(
            data_dir=tmp_dir,
            db_file="runtime_lifecycle_test.db",
            init_schema_func=init_runtime_schema_sync,
        )
        try:
            agent_id = "agent-life-5"
            subagent_id = "main-agent-li"
            _insert_agent_and_subagent(agent_id, subagent_id)
            repo = RuntimeRepository(get_db())
            runtime = repo.create_runtime(subagent_id, agent_id, [])

            def _to_completed():
                local_repo = RuntimeRepository(get_db())
                return local_repo.cas_set_status(runtime.runtime_id, ["active"], "completed")

            def _to_failed():
                local_repo = RuntimeRepository(get_db())
                return local_repo.cas_set_status(runtime.runtime_id, ["active"], "failed")

            with ThreadPoolExecutor(max_workers=2) as pool:
                completed_future = pool.submit(_to_completed)
                failed_future = pool.submit(_to_failed)
                completed_ok = completed_future.result()
                failed_ok = failed_future.result()

            # Only one competing CAS write should succeed.
            assert int(completed_ok) + int(failed_ok) == 1
            final_runtime = repo.get_by_id(runtime.runtime_id)
            assert final_runtime is not None
            assert final_runtime.status in {"completed", "failed"}
        finally:
            close_database()
