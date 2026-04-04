"""
Context Stack v2 — Checkpoint Blob (§8.1)

Serialization and restoration of engine state for cross-process recovery.

Blob format:
  {
      "blob_version": 1,
      "engine_config_hash": "sha256:...",
      "stack_frames": [...],
      "sessions": {scope_id: {...}},
      "stats": {...},
      "meta": {...}
  }

Design decisions:
  - Messages are NOT stored in the blob (too large); host provides them on restore
  - Config hash validation prevents restoring into incompatible engine
  - blob_version enables forward-compatible upgrades
  - Stash segments (§4.6.8) not yet included (M3 note: nested fold off by default)
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from .types import (
    Message,
    MessageRole,
    ScopePhase,
    ScopeState,
    StackFrame,
)
from .config import CompactConfig

logger = logging.getLogger("context_stack.v2.blob")

# Current blob format version
BLOB_VERSION = 1


class CheckpointBlobError(Exception):
    """Base error for checkpoint blob operations."""
    pass


class BlobVersionError(CheckpointBlobError):
    """Blob version incompatible with this engine."""
    pass


class BlobConfigHashError(CheckpointBlobError):
    """Engine config hash doesn't match blob."""
    pass


class BlobCorruptedError(CheckpointBlobError):
    """Blob data is corrupted or tampered with."""
    pass


# ─────────────────────────────────────────────
# Config Hash (§8.1)
# ─────────────────────────────────────────────

def compute_config_hash(config: CompactConfig) -> str:
    """
    Compute a stable SHA-256 hash of the engine configuration.

    Fields that participate in the hash are sorted alphabetically
    to ensure deterministic output across Python versions.

    Returns:
        "sha256:<hex>" prefixed hash
    """
    # Collect all config fields that affect serialization/behavior
    fields = {
        "context_window": config.context_window,
        "compact_threshold": config.compact_threshold,
        "emergency_threshold": config.emergency_threshold,
        "micro_max_tool_output_chars": config.micro_max_tool_output_chars,
        "micro_preserve_recent": config.micro_preserve_recent,
        "auto_summary_max_tokens": config.auto_summary_max_tokens,
        "scope_store_raw": config.scope_store_raw,
        "raw_max_chars_per_scope": config.raw_max_chars_per_scope,
        "full_prefix_validation": config.full_prefix_validation,
        "auto_meta_when_stack_empty": config.auto_meta_when_stack_empty,
        "auto_meta_explicit_mode": config.auto_meta_explicit_mode,
        "max_skill_depth": config.max_skill_depth,
        "max_skill_end_retries": config.max_skill_end_retries,
        "skill_end_empty_fallback": config.skill_end_empty_fallback,
        "nested_skill_fold": config.nested_skill_fold,
        "nested_fold_summarizer": config.nested_fold_summarizer,
        "nested_fold_stash_threshold": config.nested_fold_stash_threshold,
    }

    # Sorted JSON for determinism
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return f"sha256:{digest}"


# ─────────────────────────────────────────────
# Frame serialization
# ─────────────────────────────────────────────

def _serialize_frame(frame: StackFrame) -> Dict[str, Any]:
    """Serialize a StackFrame to a dict."""
    d = {
        "scope_id": frame.scope_id,
        "skill_name": frame.skill_name,
        "skill_type": frame.skill_type,
        "auto_meta": frame.auto_meta,
        "message_start_idx": frame.message_start_idx,
        "prefix_hash": frame.prefix_hash,
        "depth": frame.depth,
        "started_at": frame.started_at,
        "folded_until_child": frame.folded_until_child,
    }
    # Stash: only ref/hash (not inline segment for blob portability)
    if frame.stash_ref:
        d["stash_ref"] = frame.stash_ref
        d["stash_hash"] = frame.stash_hash
    return d


def _deserialize_frame(d: Dict[str, Any]) -> StackFrame:
    """Deserialize a dict to a StackFrame."""
    return StackFrame(
        scope_id=d["scope_id"],
        skill_name=d["skill_name"],
        skill_type=d["skill_type"],
        auto_meta=d.get("auto_meta", False),
        message_start_idx=d.get("message_start_idx", 0),
        prefix_hash=d.get("prefix_hash", ""),
        depth=d.get("depth", 0),
        started_at=d.get("started_at", time.time()),
        stash_ref=d.get("stash_ref"),
        stash_hash=d.get("stash_hash"),
        folded_until_child=d.get("folded_until_child", False),
    )


# ─────────────────────────────────────────────
# Session state serialization
# ─────────────────────────────────────────────

def _serialize_session_state(session) -> Dict[str, Any]:
    """Serialize a ScopeSession's state (not the session object itself)."""
    return {
        "scope_id": session.scope_id,
        "phase": session.phase.value,
        "turn_count": session._turn_count,
        "last_idempotency_key": (
            sorted(session._idempotency_keys)[-1]
            if session._idempotency_keys else None
        ),
        "idempotency_keys": sorted(session._idempotency_keys),
        "scope_name": session.scope.name,
        "scope_skill_name": session.scope.skill_name,
        "scope_started_at": session.scope.started_at,
        "scope_message_start_idx": session.scope.message_start_idx,
        "scope_tokens_before": session.scope.tokens_before,
    }


# ─────────────────────────────────────────────
# Blob create / restore
# ─────────────────────────────────────────────

def create_checkpoint_blob(
    engine,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a checkpoint blob from the current engine state.

    The blob contains everything needed to restore the engine
    to its current state (minus the actual messages, which the
    host provides on restore).

    Args:
        engine: ContextEngine instance
        meta: optional metadata (task_id, correlation_id, etc.)

    Returns:
        Serializable dict (ready for json.dumps / msgpack)
    """
    config_hash = compute_config_hash(engine._config)

    # Serialize stack frames
    stack_frames = [
        _serialize_frame(f) for f in engine._stack.frames
    ]

    # Serialize session states
    sessions = {
        scope_id: _serialize_session_state(session)
        for scope_id, session in engine._sessions.items()
    }

    # Stats
    with engine._stats_lock:
        stats = {
            "total_tokens_saved": engine._total_tokens_saved,
            "total_lifecycles": engine._total_lifecycles,
        }

    blob = {
        "blob_version": BLOB_VERSION,
        "engine_config_hash": config_hash,
        "created_at": time.time(),
        "stack_frames": stack_frames,
        "sessions": sessions,
        "stats": stats,
        "meta": meta or {},
    }

    logger.info(
        "Checkpoint blob created: frames=%d sessions=%d hash=%s",
        len(stack_frames), len(sessions), config_hash[:20],
    )
    return blob


def validate_blob(blob: Dict[str, Any], config: CompactConfig) -> None:
    """
    Validate a checkpoint blob before attempting restore.

    Raises:
        BlobVersionError: if blob version is incompatible
        BlobConfigHashError: if config hash doesn't match
        BlobCorruptedError: if blob structure is invalid
    """
    # Version check
    version = blob.get("blob_version")
    if version is None:
        raise BlobCorruptedError("Missing 'blob_version' in checkpoint blob.")
    if version > BLOB_VERSION:
        raise BlobVersionError(
            f"Blob version {version} is newer than supported version "
            f"{BLOB_VERSION}. Upgrade context-stack to restore this blob."
        )
    if version < 1:
        raise BlobVersionError(f"Invalid blob version: {version}")

    # Config hash check
    expected_hash = compute_config_hash(config)
    actual_hash = blob.get("engine_config_hash", "")
    if actual_hash != expected_hash:
        raise BlobConfigHashError(
            f"Engine config hash mismatch. "
            f"Blob: {actual_hash[:30]}..., "
            f"Current: {expected_hash[:30]}... "
            f"Cannot restore into engine with different configuration."
        )

    # Structure check
    required = {"blob_version", "engine_config_hash", "stack_frames", "sessions"}
    missing = required - set(blob.keys())
    if missing:
        raise BlobCorruptedError(
            f"Checkpoint blob missing required fields: {missing}"
        )

    if not isinstance(blob["stack_frames"], list):
        raise BlobCorruptedError("'stack_frames' must be a list.")
    if not isinstance(blob["sessions"], dict):
        raise BlobCorruptedError("'sessions' must be a dict.")


def restore_from_blob(
    engine,
    blob: Dict[str, Any],
    messages: List[Message],
) -> None:
    """
    Restore engine state from a checkpoint blob.

    The host must provide the current messages (not stored in blob).
    Only sessions in EXECUTING phase can be restored.

    Args:
        engine: ContextEngine instance (should be fresh/empty)
        blob: the checkpoint blob dict
        messages: current conversation messages from host

    Raises:
        BlobVersionError, BlobConfigHashError, BlobCorruptedError
        RuntimeError: if engine is not in a restorable state
    """
    from .scope_session import ScopeSession

    # Validate
    validate_blob(blob, engine._config)

    # Check engine is clean
    if engine._stack.depth > 0:
        raise RuntimeError(
            "Cannot restore: engine already has active scopes. "
            "Close or create a new engine instance."
        )

    # Restore stack frames
    for frame_data in blob["stack_frames"]:
        frame = _deserialize_frame(frame_data)
        engine._stack._frames.append(frame)

    # Restore sessions (only EXECUTING ones can be resumed)
    for scope_id, session_data in blob["sessions"].items():
        phase_str = session_data.get("phase", "executing")
        if phase_str not in ("executing", "pre"):
            logger.warning(
                "Skipping non-resumable session: scope=%s phase=%s",
                scope_id, phase_str,
            )
            continue

        # Find matching frame
        matching_frame = None
        for frame in engine._stack._frames:
            if frame.scope_id == scope_id:
                matching_frame = frame
                break

        if not matching_frame:
            logger.warning(
                "No stack frame for session '%s', skipping.", scope_id,
            )
            continue

        # Reconstruct session
        session = ScopeSession(
            frame=matching_frame,
            config=engine._config,
            checkpoint_mgr=engine._checkpoint,
            counter=engine._counter,
            store=engine._store,
        )

        # Restore session internal state
        session._scope.id = scope_id
        session._scope.name = session_data.get("scope_name", matching_frame.skill_name)
        session._scope.skill_name = session_data.get("scope_skill_name", matching_frame.skill_name)
        session._scope.started_at = session_data.get("scope_started_at", time.time())
        session._scope.message_start_idx = session_data.get(
            "scope_message_start_idx",
            matching_frame.message_start_idx,
        )
        session._scope.tokens_before = session_data.get("scope_tokens_before", 0)
        session._scope.state = ScopeState.OPEN

        session._turn_count = session_data.get("turn_count", 0)
        session._idempotency_keys = set(session_data.get("idempotency_keys", []))

        # Force phase to EXECUTING (skip INIT→PRE transition)
        session._phase = ScopePhase.EXECUTING

        engine._sessions[scope_id] = session

    # Restore stats
    stats = blob.get("stats", {})
    with engine._stats_lock:
        engine._total_tokens_saved = stats.get("total_tokens_saved", 0)
        engine._total_lifecycles = stats.get("total_lifecycles", 0)

    logger.info(
        "Restored from blob: frames=%d sessions=%d",
        engine._stack.depth, len(engine._sessions),
    )


def compute_blob_hash(blob: Dict[str, Any]) -> str:
    """
    Compute a SHA-256 hash of the blob for integrity verification.

    Used in transit/storage to detect tampering (§2.3).
    """
    canonical = json.dumps(blob, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
