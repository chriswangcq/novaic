# API contracts (novaic_cortex — Wave 3)

Public shapes below match the current package implementation. Use `async` where shown.

## CortexStore

Abstract backend for object storage (`novaic_cortex.store.CortexStore`):

- `put`, `get`, `get_text`, `exists`, `delete`
- `list_objects(prefix, delimiter="/")`, `list_recursive(prefix)`
- `put_json`, `get_json`, `copy`, `move`, `move_prefix` → `int` count

Concrete implementations: `MemoryStore`, `LocalFileStore`. **`S3Store`** (`novaic_cortex.s3_store`) is an optional boto3-backed implementation (install extra `novaic-cortex[s3]`).

**Alibaba Cloud OSS (Hong Kong default):** `novaic_cortex.aliyun_oss_s3.s3_store_aliyun_oss()` builds an `S3Store` with a boto3 client pointed at `https://oss-cn-hongkong.aliyuncs.com`, default bucket `novaic-s3-bucket`, default logical prefix `cortex/`. Credentials: `ALIBABA_CLOUD_ACCESS_KEY_ID` / `ALIBABA_CLOUD_ACCESS_KEY_SECRET`, or `key_file=` with `accessKeyId` / `accessKeySecret` lines. Override with `NOVAIC_OSS_BUCKET`, `NOVAIC_OSS_PREFIX`, `NOVAIC_OSS_ENDPOINT`, `NOVAIC_OSS_REGION`.

Keys are full store paths, e.g. `agents/{agent_id}/rw/active/{scope_id}/messages.jsonl`.

**Backend differences:** `list_objects` only supports `delimiter="/"` (other delimiters raise `NotImplementedError` on some backends). `move_prefix` return value counts **individual file objects** moved on all backends (`MemoryStore`, `LocalFileStore`, `S3Store`). `S3Store.move(src, dst)` where `src == dst` skips the copy and deletes the source (object disappears); this avoids the S3 `InvalidRequest` error for same-key copies.

**Thread safety & concurrency:** `MemoryStore` is **not thread-safe**: its internal `dict` is unprotected by any lock, and concurrent writes from multiple async tasks or threads may corrupt state. `LocalFileStore` uses process-local paths and has no file-locking; concurrent async callers on the same instance may race on read-modify-write operations. For production multi-tenant workloads, serialize access per agent or use `S3Store`, which delegates to boto3 thread-pooled I/O with eventual consistency guarantees.

## Workspace(`store`, `agent_id`, `hooks=None`)

Maps logical `/ro/...` and `/rw/...` paths under `agents/{agent_id}/`.

**`agent_id` rules:** must be a non-empty `str`, no NUL, no `/`, no `..`.

**Read:** `read`, `read_bytes`, `list_dir`, `exists` for paths under `/ro` or `/rw`.

**Write:** `write`, `write_bytes`, `write_json`, `append_line`, `delete` — only under `/rw/`; otherwise `PermissionError`. `append_line` uses a tight read-modify-write cycle (catches `KeyError` on missing file, no separate `exists()` check), eliminating a TOCTOU gap. Not truly atomic on S3 (no CAS), but minimizes the race window.

**Scopes:** `create_scope(scope_id, name, skill="")` also creates empty `messages.jsonl`, `scratch/.keep`, and `steps/.keep` under the active scope; `archive_scope(scope_id, summary)`, `list_active_scopes`, `get_scope_depth`.

**Steps (execution timeline):** Each scope contains a `steps/` subdirectory that records execution events in chronological order. Files are named `{seq:04d}_{type}_{id}.json` (e.g. `0001_tool_tc_search.json`, `0002_scope_child_A.json`). Two step types: `"tool"` (structured tool call result, keyed by `call_id`) and `"scope"` (child scope lifecycle, keyed by child `scope_id`). The `seq` field is auto-assigned by `write_step`. Steps travel with the scope on archival via `move_prefix` — zero extra code. `list_steps(scope_id, archived=False)` returns filenames in chronological order.

**Step Index (`steps/_index.jsonl`):** Append-only JSONL file maintained by `write_step`. Each line is a lightweight metadata record (`seq`, `type`, `id`, `status`, `ts`, `file`, and optional `tool`/`duration_ms`/`result_id`/`has_artifacts`). The index provides a single-read overview of the entire step timeline without enumerating individual files. `read_step_index(scope_id, archived=False)` returns a `list[dict]`. The index file is excluded from `list_steps` results and step counting.

**Scope Outcome (`outcome.json`):** Machine-readable structured aggregate written by `archive_scope` just before the `move_prefix` to `/ro/`. Fields: `status` (`"completed"` | `"partial"` | `"failed"` | `"empty"`), `steps_total`, `steps_succeeded`, `steps_failed`, `started_at`, `ended_at`, `duration_s`, `artifacts` (aggregated from all steps with `has_artifacts`), `error` (last failed step id or `null`). `read_outcome(scope_id, archived=True)` returns the dict or `None`. Complements `summary.md` (prose for LLM/fusion) with structured data for programmatic consumption.

**Lifecycle:** `initialize()` creates placeholder trees (`.keep` files) for standard agent prefixes.

**Hooks:** optional `CortexHooks`. The workspace uses an internal `Workspace._emit(hook_list_name, *args)` helper: it resolves `getattr(hooks, hook_list_name)` as a list of callbacks, runs each (awaiting if async), and warns on failure without breaking the caller.

**`on_scope_created`:** emitted from `create_scope` with `(scope_id, meta_dict)`.

**`on_scope_archived`:** **not** emitted from `Workspace`; archival hooks run in `Compactor.compact` after `archive_scope` returns.

## Sandbox(`workspace`, `max_sync_bytes=None`, `max_wall_timeout=None`, `token_factory=None`, `cortex_api_url="http://localhost:19996"`)

**Disposable execution:** Each `exec()` is a fully independent lifecycle — no blob cache, no cross-exec state. Fresh temp dir created and destroyed per call.

- `exec(command, timeout=30, cwd=None)` → `ShellResult` (`stdout`, `stderr`, `exit_code`, `files_changed`).

**Full sync cycle (each `exec`):**

1. If `max_wall_timeout` is set, effective shell timeout is `min(timeout, max_wall_timeout)`.
2. If `max_sync_bytes` is set, compute total bytes of all objects under the agent’s `ro/` and `rw/` store prefixes (skipping empty `.keep` blobs); if over the limit, raise `ValueError` before materializing.
3. Create a fresh temp directory with `ro/` and `rw/` subdirs; copy every store object under those prefixes into the mirror (skipping zero-byte `.keep` files). **No caching** — every exec re-downloads from store.
4. Snapshot `rw/` file stats `(mtime_ns, size)` per relative path.
5. Run the subprocess with `cwd` resolved under the temp `rw` (default `rw` root); env includes `RO`, `RW`, `HOME`, `NOVAIC_API`, and optionally `NOVAIC_TOKEN` (from `token_factory()`).
6. After the command, diff the `rw` snapshot: deleted files → `Workspace.delete` on logical `/rw/...`; new or changed files → `Workspace.write_bytes`.
7. `files_changed` lists logical `/rw/...` paths that were **created, modified (mtime/size), or deleted** relative to the pre-exec snapshot.
8. Temp tree is destroyed — no state survives.

Invalid `cwd` (not a directory under `rw`) yields `ShellResult` with `exit_code=-2` and an error message in `stderr`, without running the shell.

**`token_factory`:** optional callable returning a JWT string. When set, `$NOVAIC_TOKEN` is injected into the subprocess env for CLI tool authentication with Gateway.

**`cortex_api_url`:** base URL for Cortex HTTP API, injected as `$NOVAIC_API`. Defaults to `http://localhost:19996`. Sandbox CLI calls Cortex directly (not Gateway).

## Compactor(`workspace`, `summarizer=None`, `fusion_factor=5`, `hooks=None`, `gem_fusion_enabled=True`, `gem_fusion_max_level=10`, `metrics=None`, `summarizer_max_tokens=2000`)

- `compact(scope_id, report=None)` → `CompactResult` with `scope_id`, `summary`, `archive_path` (logical path under `/ro/scopes/...`).

Summary selection: `report` if provided; else `await summarizer.summarize(messages_text, max_tokens=summarizer_max_tokens)` if `summarizer` is set; else a short deterministic fallback string.

After `summary` is chosen, if `metrics` is set: `total_tokens_saved += max(0, estimate_tokens(messages_text) - estimate_tokens(summary))` when that difference is positive.

Before archival, if `meta.json` exists, merges **compaction metadata** under `meta["compaction"]` (preserving any existing keys in that object):

- `message_chars` — length of messages text
- `summary_chars` — length of summary text
- `message_lines` — `messages_text.count("\n") + 1` when messages are non-empty, else `0`
- `files_changed` / `tools_used` — optional lists parsed from JSONL lines (OpenAI-style `tool_calls`, or top-level `files_changed` / `files` arrays when present)

Top-level `meta["files"]` / `meta["tools"]` mirror those lists when non-empty (design §4.4 metadata).

Then calls `workspace.archive_scope`, emits **`on_scope_archived`** via internal `_emit` with `(scope_id, summary, archive_path)`, logs `scope.archived` (includes `summary_len`, `messages` line count, `duration_s` from archived `meta` when available), and may run gem fusion.

**Gem fusion (when enabled, `fusion_factor > 0`):** for each level `L` from `1` through `gem_fusion_max_level`, may create at most **one** new `fuse_L{L}_{seq}` per compaction when there are **more** complete batches of children than existing `fuse_L{L}_*` nodes (avoids re-fusing a steady child count). L1 children are raw `/ro/scopes/{id}/` folders (excluding `__fused__`); deeper levels fuse `fuse_L{L-1}_*` under `__fused__/`. L1 batch selection orders by `ended_at` then id; deeper levels use sorted child folder names. Successful fusions increment `metrics.total_fusions` and `metrics.max_fusion_level` when `metrics` is provided. **`on_fusion`** receives `(fuse_folder_name, children_ids)`. An internal `_fuse_counts_cache` avoids redundant `list_recursive(__fused__)` scans when the cached batch count already shows no fusion is needed.

## Recall(`workspace`, `token_budget=4000`, `token_counter=None`)

- `generate()` → `str` (markdown sections for fuzzy memory, skills, config), assembled with `---` separators and approximate token budgeting via `estimate_tokens` (~chars//4). Per-section budget is derived from `token_budget` (memory/skills/config each get about one third of the total). Config includes **`personality.md`**, **`constraints.md`** (if present), and **`engine.json`** (pretty-printed when valid JSON). Truncation appends `[truncated]` when needed.

**`token_counter`:** optional `novaic_cortex.protocols.TokenCounter`. When provided, implementations may use it for budgeting or diagnostics where a host-specific tokenizer is required; when omitted, behavior matches token estimation via `estimate_tokens` only.

## Cortex(`store`, `agent_id`, `summarizer=None`, `hooks=None`, `metrics=None`, `token_counter=None`)

Façade wiring `Workspace`, `Sandbox`, `Recall`, `Compactor`. Default `hooks` and `metrics` are new empty `CortexHooks` / `CortexMetrics` instances.

**`token_counter`:** optional; passed through to `Recall` so the host can supply a `TokenCounter` implementation. Omitted means `Recall` uses default estimation only.

**`initialize()`:** `await workspace.initialize()`, then `self.config = await load_engine_config(workspace)` and rebuilds `Sandbox` / `Recall` / `Compactor` from that config (timeouts, token budget, fusion flags/factors/levels, **`summarizer_max_tokens = config.auto_summary_max_tokens`**). Rebuilt `Recall` preserves the same `token_counter` wiring as at construction.

**Tool path rules:** `tool_read` and `tool_write` require `path.strip()` to start with `/ro/` or `/rw/`; otherwise `ValueError`. Writes still obey workspace rules (`/rw/` only for mutating ops).

**`tool_shell(command, timeout=None)`:** if `timeout` is omitted and `self.config` is set, uses `config.sandbox_timeout_default`; else default `30`. If `self.config` is set, uses `min(effective_timeout, config.sandbox_timeout_max)` before delegating to `sandbox.exec`.

**`tool_read`:** after `initialize()`, if `len(text) > config.micro_max_tool_output_chars`, returns a prefix plus a `[truncated by micro_max_tool_output_chars]` suffix.

**Agent-facing tool API (3-tool model):** `skill_begin(name)` → `{"ok", "instance_id", "name", "tools"}` (creates scope internally, increments `metrics.scopes_created`); `skill_end(instance_id, report)` → `{"ok", "instance_id", "archive_path"}` or `{"ok": false, "warning": ...}` on LIFO violation (increments `metrics.scopes_archived` and `metrics.compactions_completed`). **Internal scope API:** `scope_create(scope_id, name, skill, parent_path)` → scope base path; `scope_end(scope_id, report)` → `{"ok", "scope_id", "archive_path"}`. **Other:** `prepare_system_prompt()` → `recall.generate()` (increments `metrics.recall_generations`); `install_skill` enforces `max_skill_depth` against slash segments in `name`, runs `on_skill_loaded` hooks (sync/async with `UserWarning` on failure), increments `metrics.skills_installed`; `_rebuild_skill_index` as in `runtime.py`.

**`TOOL_SCHEMAS`:** three tools — `shell`, `skill_begin`, `skill_end` — see `novaic_cortex.tool_schemas`.

## EngineConfig / `load_engine_config`

Defined in **`novaic_cortex.config`**: `EngineConfig` dataclass defaults and `load_engine_config(workspace)` reading `/ro/config/engine.json` (missing file → defaults; invalid JSON syntax → `UserWarning` + defaults; invalid top-level JSON type → `ValueError`). See that module for field names and merge behavior.

**Wiring notes:** `micro_preserve_recent` is reserved for future host-side message windowing (not used inside `Recall` today). `sandbox_timeout_default` drives the default `tool_shell` timeout after `initialize()`.

## Observability: `log_cortex`

`novaic_cortex.observability.log_cortex(event, **kwargs)` logs one INFO line: `[CORTEX] {event}` plus `k=v` pairs (repr truncated per value).

Events used in the current codebase include:

- `scope.created` — scope lifecycle (from `Workspace.create_scope`)
- `scope.archived` — after compaction archival (`summary_len`, `messages`, `duration_s`, …)
- `fusion.triggered` — gem fusion at any implemented level
- `sandbox.exec` — command snippet, `exit_code`, `duration_ms`, `duration_s`
- `recall.generated` — section count and approximate tokens

## CortexMetrics

`novaic_cortex.types.CortexMetrics` fields:

- `scopes_created`
- `scopes_archived`
- `total_fusions`
- `max_fusion_level`
- `shell_executions`
- `shell_timeouts`
- `total_files_read`
- `total_files_written`
- `recall_generations`
- `total_tokens_saved`
- `skills_installed` — incremented on each successful `Cortex.install_skill`
- `compactions_completed` — incremented on each successful `scope_end` / `skill_end` / `compact`

Helper: `metrics_as_dict(CortexMetrics) -> dict[str, int]` (integer fields only).

## TenantLayout(`user_id`, `agent_id`, `bucket="novaic-s3-bucket"`)

Frozen dataclass in `novaic_cortex.tenant` that derives S3 key prefixes for multi-tenant storage from `(user_id, agent_id)`.

**Validation:** `user_id` and `agent_id` follow the same rules as `Workspace.agent_id` — non-empty string, no `/`, `..`, or NUL.

**Properties:**

- `store_prefix` → `"users/{user_id}/"` — full S3 prefix for one user's Cortex data (pass to `S3Store(bucket, prefix=...)`)
- `attachments_prefix` → `"users/{user_id}/attachments/"` — S3 prefix for File Service binary assets
- `user_prefix` → `"users/{user_id}/"` — top-level namespace for the user

See `docs/oss-storage-unified-plan.md` §6.1 for the design rationale and directory layout.

## Context budget

Pure helpers in **`novaic_cortex.context_budget`** for hosts that already know approximate **used token** counts (Cortex does not track full chat context usage).

- **`usage_ratio(used_tokens, context_window) -> float`** — When `context_window > 0`: `min(1.0, max(0, used_tokens) / context_window)` so the ratio stays in `[0, 1]` even if the host passes a negative estimate; when `context_window <= 0`, `0.0`.
- **`compact_level(used_tokens, cfg: EngineConfig) -> Literal["none", "normal", "emergency"]`** — Uses `usage_ratio` against `cfg.context_window`, then compares to `cfg.emergency_threshold` and `cfg.compact_threshold` (emergency wins when both apply).

**`Cortex.suggest_compact(used_tokens) -> dict`** — Async; uses cached `self.config` after `initialize()`, or default `EngineConfig()` before. Returns `usage_ratio`, `level` (`compact_level`), `context_window`, `compact_threshold`, `emergency_threshold`. Side-effect free (no store I/O); hosts decide when to act (e.g. call `scope_end`).
