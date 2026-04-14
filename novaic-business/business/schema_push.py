"""
Push ALL entity schemas to Entangled from Business Service.

Business is the sole schema owner for all Entangled-managed entities.
Gateway no longer pushes schemas; it only keeps EntityDef registrations
for its own RemoteEntityStore serialisation.

Entity definitions use entangled.sql types (pure dataclasses, no gateway imports).
"""

import json as _json
import logging
import urllib.request
from typing import Optional

from common.config import ServiceConfig
from entangled.sql.field_def import FieldDef, FieldKind, F
from entangled.sql.entity_def import SqlEntityDef

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Entity Definitions — previously split across gateway/entity/defs_*.py
# ═══════════════════════════════════════════════════════════════════════════════

# ── Skills + API Keys (already owned by Business) ─────────────────────────────

SKILLS_DEF = SqlEntityDef(
    name="skills",
    table="skills",
    id_field="id",
    user_scoped=True,
    key_params=[],
    subscription_mode="eager",
    default_order="created_at",
    fields=[
        F.text("id", primary=True),
        F.text("user_id", nullable=False, default="", index=True, ref="users(id) ON DELETE CASCADE"),
        F.text("name", nullable=False),
        F.text("description", default=""),
        F.text("prompt", default=""),
        F.json("tools", default="[]"),
        F.text("workflow", default=""),
        F.text("icon", default="zap"),
        F.bool_("enabled", default=True),
        F.text("source", default="custom"),
        F.text("builtin_id"),
        F.text("forked_from"),
        F.json("auto_match_keywords", default="[]"),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
)

API_KEYS_DEF = SqlEntityDef(
    name="api-keys",
    table="api_keys",
    id_field="id",
    user_scoped=True,
    key_params=[],
    subscription_mode="eager",
    default_order="created_at",
    fields=[
        F.text("id", primary=True),
        F.text("user_id", nullable=False, default="", index=True, ref="users(id) ON DELETE CASCADE"),
        F.text("name", nullable=False),
        F.text("provider", nullable=False, index=True),
        F.text("api_key", hidden=True),
        F.bool_("has_api_key", default=False),
        F.text("api_base"),
        F.text("deployment_name"),
        F.text("api_version"),
        F.timestamp("created_at"),
    ],
)

# ── Agents core ───────────────────────────────────────────────────────────────

AGENTS_DEF = SqlEntityDef(
    name="agents",
    table="agents",
    id_field="id",
    user_scoped=True,
    key_params=[],
    subscription_mode="eager",
    default_order="created_at",
    fields=[
        F.text("id", primary=True),
        F.text("user_id", nullable=False, default="", index=True, ref="users(id) ON DELETE CASCADE"),
        F.text("name", nullable=False),
        F.timestamp("created_at"),
        F.bool_("setup_complete", default=False),
        F.text("model_id"),
        F.timestamp("updated_at"),
    ],
)

SUBAGENTS_DEF = SqlEntityDef(
    name="subagents",
    table="subagents",
    id_field="subagent_id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    default_order="created_at ASC",
    fields=[
        F.text("subagent_id", primary=True),
        F.text("agent_id", nullable=False, index=True, ref="agents(id) ON DELETE CASCADE"),
        F.text("type", nullable=False),
        F.text("parent_subagent_id"),
        F.text("status", default="sleeping", index=True),
        F.text("historical_summary"),
        F.json("wake_triggers", default='[{"type":"user_response"}]'),
        F.text("handoff_notes"),
        F.text("wake_at"),
        F.text("task"),
        F.text("progress"),
        F.text("result"),
        F.text("error"),
        F.text("timeout_at"),
        F.json("hrl", default="[]"),
        F.int_("summary_lock", default=0),
        F.int_("log_count", default=0),
        F.int_("need_rest", default=0),
        F.json("tool_ports"),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
)

# ── Devices / VM Users ────────────────────────────────────────────────────────

DEVICES_DEF = SqlEntityDef(
    name="devices",
    table="devices",
    id_field="id",
    user_scoped=True,
    key_params=[],
    subscription_mode="eager",
    default_order="created_at",
    fields=[
        F.text("id", primary=True),
        F.text("user_id", nullable=False, default="", index=True, ref="users(id) ON DELETE CASCADE"),
        F.text("type", nullable=False),
        F.text("name", default=""),
        F.timestamp("created_at"),
        F.text("status", default="created"),
        F.int_("memory", default=4096),
        F.int_("cpus", default=4),
        F.text("data_path", default=""),
        F.json("ports", default="{}"),
        F.text("backend", default="qemu"),
        F.text("os_type", default="ubuntu"),
        F.text("os_version", default="24.04"),
        F.text("image_path", default=""),
        F.bool_("cloud_init_complete", default=False),
        F.text("avd_name", default=""),
        F.text("device_serial", default=""),
        F.bool_("managed", default=True),
        F.text("system_image", default=""),
        F.text("pc_client_id"),
        F.timestamp("updated_at"),
    ],
    constraints=[
        "CHECK(type IN ('linux', 'android', 'host_desktop'))",
        "CHECK(status IN ('created', 'setup', 'ready', 'running', 'stopped', 'error'))",
    ],
)

VM_USERS_DEF = SqlEntityDef(
    name="vm-users",
    table="vm_users",
    id_field="id",
    user_scoped=False,
    key_params=["device_id"],
    parent=("devices", "device_id", "id"),
    default_order="created_at",
    fields=[
        F.text("id", primary=True),
        F.text("device_id", nullable=False, index=True, ref="devices(id) ON DELETE CASCADE"),
        F.text("username", nullable=False),
        F.text("password", nullable=False, default="", hidden=True),
        F.int_("display_num", default=11),
        F.timestamp("created_at"),
    ],
    constraints=["UNIQUE(device_id, username)"],
)

# ── Files ─────────────────────────────────────────────────────────────────────

FILES_DEF = SqlEntityDef(
    name="files",
    table="files",
    id_field="id",
    user_scoped=True,
    key_params=[],
    subscription_mode="eager",
    default_order="created_at DESC",
    fields=[
        F.text("id", primary=True),
        F.text("user_id", nullable=False, default="", index=True),
        F.text("agent_id", index=True),
        F.text("category", nullable=False, default="chat_attachments"),
        F.text("mime_type", nullable=False, default="application/octet-stream"),
        F.int_("size", default=0),
        F.text("filename"),
        F.text("storage_backend", nullable=False, default="local"),
        F.text("storage_key", nullable=False),
        F.timestamp("created_at"),
    ],
)

# ── Users / Preferences / Agent-Skills ────────────────────────────────────────

USER_PREFERENCES_DEF = SqlEntityDef(
    name="user-preferences",
    table="user_preferences",
    id_field="user_id",
    user_scoped=True,
    parent=("users", "user_id", "id"),
    subscription_mode="eager",
    default_order="updated_at",
    fields=[
        F.text("user_id", primary=True, ref="users(id) ON DELETE CASCADE"),
        F.text("default_model", default="gpt-4o"),
        F.text("audio_model"),
        F.int_("max_tokens", default=4096),
        F.int_("max_iterations", default=20),
        F.bool_("visible_shell", default=False),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
)

AGENT_SKILLS_DEF = SqlEntityDef(
    name="agent-skills",
    table="agent_skills",
    id_field="skill_id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    default_order="priority ASC",
    fields=[
        F.text("agent_id", nullable=False, index=True, ref="agents(id) ON DELETE CASCADE"),
        F.text("skill_id", nullable=False, index=True, ref="skills(id) ON DELETE CASCADE"),
        F.int_("priority", default=0),
        F.timestamp("created_at"),
    ],
)

# ── Models ────────────────────────────────────────────────────────────────────

MODELS_DEF = SqlEntityDef(
    name="models",
    table="models",
    id_field="model_id",
    user_scoped=False,
    key_params=[],
    subscription_mode="eager",
    default_order="name",
    fields=[
        F.text("model_id", primary=True),
        F.text("name", nullable=False),
        F.text("provider", nullable=False),
        F.int_("is_custom", default=0),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
)

API_KEY_MODELS_DEF = SqlEntityDef(
    name="api-key-models",
    table="api_key_models",
    id_field="id",
    user_scoped=True,
    key_params=["api_key_id"],
    parent=("api-keys", "api_key_id", "id"),
    subscription_mode="eager",
    default_order="created_at",
    fields=[
        F.text("id", primary=True),
        F.text("user_id", nullable=False, index=True, ref="users(id) ON DELETE CASCADE"),
        F.text("api_key_id", nullable=False, index=True, ref="api_keys(id) ON DELETE CASCADE"),
        F.text("model_id", nullable=False, index=True),
        F.timestamp("created_at"),
    ],
    constraints=["UNIQUE(api_key_id, model_id)"],
)

AVAILABLE_MODELS_DEF = SqlEntityDef(
    name="available-models",
    table="available_models",
    id_field="id",
    user_scoped=True,
    key_params=[],
    subscription_mode="eager",
    default_order="created_at",
    fields=[
        F.text("id", primary=True),
        F.text("user_id", nullable=False, index=True, ref="users(id) ON DELETE CASCADE"),
        F.text("model_id", nullable=False, index=True),
        F.text("api_key_id", nullable=False, index=True, ref="api_keys(id) ON DELETE CASCADE"),
        F.timestamp("created_at"),
    ],
    constraints=["UNIQUE(user_id, model_id)"],
)

# ── Agent Forms ───────────────────────────────────────────────────────────────

AGENT_BINDING_DEF = SqlEntityDef(
    name="agent-binding",
    table="agent_device_bindings",
    id_field="agent_id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    subscription_mode="eager",
    default_order="created_at",
    fields=[
        F.text("agent_id", primary=True, ref="agents(id) ON DELETE CASCADE"),
        F.text("device_id", nullable=False, index=True, ref="devices(id) ON DELETE CASCADE"),
        F.text("subject_type", nullable=False),
        F.text("subject_id", nullable=False, default=""),
        F.json("mounted_tools", default="[]"),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
)

AGENT_TOOLS_DEF = SqlEntityDef(
    name="agent-tools",
    table="agent_drive",
    id_field="agent_id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    default_order="created_at",
    fields=[
        F.text("agent_id", primary=True, ref="agents(id) ON DELETE CASCADE"),
        F.json("personality", default="{}"),
        F.text("communication_style", default="friendly"),
        F.json("user_profile", default="{}"),
        F.text("user_active_hours"),
        F.real("proactiveness", default=0.5),
        F.int_("min_rest_minutes", default=15),
        F.int_("max_rest_minutes", default=120),
        F.int_("relationship_level", default=0),
        F.int_("interaction_count", default=0),
        F.int_("no_response_streak", default=0),
        F.text("last_proactive_at"),
        F.json("enabled_tool_categories", default="[]"),
        F.json("disabled_tools", default="[]"),
        F.text("custom_instructions", default=""),
        F.text("soul_md", default=""),
        F.text("heartbeat_md", default=""),
        F.text("memory_md", default=""),
        F.text("user_md", default=""),
        F.text("behavior_guide_md", default=""),
        F.text("capability_list_md", default=""),
        F.text("sub_subagent_guide_md", default=""),
        F.text("active_hours_start", default="09:00"),
        F.text("active_hours_end", default="22:00"),
        F.text("active_hours_timezone", default="Asia/Shanghai"),
        F.json("growth_log", default="[]"),
        F.json("drive_config", default="{}"),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
)

AGENT_STATE_DEF = SqlEntityDef(
    name="agent-state",
    table="agent_state",
    id_field="agent_id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    default_order="last_active_at",
    fields=[
        F.text("agent_id", primary=True, ref="agents(id) ON DELETE CASCADE"),
        F.text("state", default="awake"),
        F.json("wake_triggers", default="[]"),
        F.text("rest_reason"),
        F.text("handoff_notes"),
        F.timestamp("rest_started_at"),
        F.timestamp("last_active_at"),
    ],
    constraints=["CHECK(state IN ('awake', 'sleep'))"],
)

AGENT_NOTEBOOK_DEF = SqlEntityDef(
    name="agent-notebook",
    table="agent_notebook",
    id_field="id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    default_order="created_at DESC",
    fields=[
        F.int_("id", primary=True),
        F.text("agent_id", ref="agents(id) ON DELETE CASCADE"),
        F.text("entry_type", default="memo"),
        F.text("title", default=""),
        F.text("content", default=""),
        F.text("source"),
        F.json("related_topics", default="[]"),
        F.real("relevance_score", default=0.5),
        F.text("status", default="draft"),
        F.timestamp("expires_at"),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
)

AGENT_MEMORY_DEF = SqlEntityDef(
    name="agent-memory",
    table="agent_memory",
    id_field="key",
    user_scoped=False,
    key_params=["agent_id", "namespace"],
    parent=("agents", "agent_id", "id"),
    default_order="updated_at DESC",
    fields=[
        F.text("agent_id", primary=True, ref="agents(id) ON DELETE CASCADE"),
        F.text("namespace", primary=True, default="default"),
        F.text("key", primary=True),
        F.json("value", default="null"),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
)

AGENT_TASKS_DEF = SqlEntityDef(
    name="agent-tasks",
    table="agent_tasks",
    id_field="id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    default_order="created_at DESC",
    fields=[
        F.int_("id", primary=True),
        F.text("agent_id", ref="agents(id) ON DELETE CASCADE"),
        F.text("title"),
        F.text("description", default=""),
        F.text("quadrant"),
        F.text("status", default="pending"),
        F.text("source"),
        F.text("reasoning"),
        F.text("due_date"),
        F.timestamp("reminder_at"),
        F.text("context"),
        F.json("related_profile_keys", default="[]"),
        F.json("progress_notes", default="[]"),
        F.timestamp("completed_at"),
        F.text("completion_notes"),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
)

# ── Stream entities ───────────────────────────────────────────────────────────

MESSAGES_DEF = SqlEntityDef(
    name="messages",
    table="chat_messages",
    id_field="id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    default_order="timestamp DESC",
    fields=[
        F.text("id", primary=True),
        F.text("agent_id", nullable=False, index=True, ref="agents(id) ON DELETE CASCADE"),
        F.text("type", nullable=False),
        F.json("content"),
        F.int_("read", default=0, index=True),
        F.json("metadata", default="{}"),
        F.text("timestamp", nullable=False, index=True),
        F.timestamp("created_at"),
        F.text("claimed_by", hidden=True),
        F.text("claimed_at", hidden=True),
        F.int_("processed", default=0, hidden=True),
        F.text("status", default="sent", index=True),
        F.timestamp("updated_at"),
    ],
)

EXECUTION_LOGS_DEF = SqlEntityDef(
    name="execution-logs",
    table="execution_logs",
    id_field="id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    default_order="timestamp ASC",
    fields=[
        F.int_("id", primary=True),
        F.text("agent_id", nullable=False, index=True, ref="agents(id) ON DELETE CASCADE"),
        F.text("subagent_id", default="main"),
        F.text("type", nullable=False),
        F.text("kind", default="tool"),
        F.text("status", default="complete"),
        F.text("event_key"),
        F.text("timestamp", nullable=False),
        F.json("data", default="{}"),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
    constraints=["UNIQUE(agent_id, subagent_id, event_key)"],
)

LOG_PAYLOADS_DEF = SqlEntityDef(
    name="log-payloads",
    table="execution_log_payloads",
    id_field="log_id",
    user_scoped=False,
    key_params=["agent_id"],
    parent=("agents", "agent_id", "id"),
    default_order="created_at",
    fields=[
        F.int_("log_id", primary=True),
        F.text("agent_id", nullable=False, index=True, ref="agents(id) ON DELETE CASCADE"),
        F.json("input", default="{}"),
        F.json("result", default="{}"),
        F.text("error"),
        F.timestamp("created_at"),
        F.timestamp("updated_at"),
    ],
    constraints=["FOREIGN KEY(log_id) REFERENCES execution_logs(id) ON DELETE CASCADE"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Complete Entity Registry + Action Hook Mapping
# ═══════════════════════════════════════════════════════════════════════════════

ALL_BUSINESS_ENTITIES = {
    "skills":            SKILLS_DEF,
    "api-keys":          API_KEYS_DEF,
    "agents":            AGENTS_DEF,
    "subagents":         SUBAGENTS_DEF,
    "devices":           DEVICES_DEF,
    "vm-users":          VM_USERS_DEF,
    "files":             FILES_DEF,
    "user-preferences":  USER_PREFERENCES_DEF,
    "agent-skills":      AGENT_SKILLS_DEF,
    "models":            MODELS_DEF,
    "api-key-models":    API_KEY_MODELS_DEF,
    "available-models":  AVAILABLE_MODELS_DEF,
    "agent-binding":     AGENT_BINDING_DEF,
    "agent-tools":       AGENT_TOOLS_DEF,
    "agent-state":       AGENT_STATE_DEF,
    "agent-notebook":    AGENT_NOTEBOOK_DEF,
    "agent-memory":      AGENT_MEMORY_DEF,
    "agent-tasks":       AGENT_TASKS_DEF,
    "messages":          MESSAGES_DEF,
    "execution-logs":    EXECUTION_LOGS_DEF,
    "log-payloads":      LOG_PAYLOADS_DEF,
}

ENTITY_ACTIONS = {
    "skills": [
        "match", "fork", "get_tool_categories",
        "get_agent_skills", "set_agent_skills",
        "get_agent_tools_config", "save_agent_tools_config",
    ],
    "api-keys": ["test"],
    "agents": ["interrupt", "init", "get_model", "prompts_preview", "available_images"],
    "user-preferences": ["get_config", "cleanup"],
    "agent-tools": ["get_bootstrap", "save_bootstrap"],
    "models": ["add_custom"],
    "api-key-models": ["refresh", "remove"],
    "available-models": ["toggle"],
    "messages": ["send", "mark_all_read", "clear"],
    "execution-logs": ["clear"],
    "log-payloads": ["get_input"],
    "devices": [
        "grouped", "setup", "start", "stop",
        "vm_start", "vm_stop", "android_start", "android_stop",
        "webrtc_stop", "get_status", "get_subjects", "get_tool_capabilities",
        "android_status",
    ],
    "vm-users": ["restart_vnc"],
}


_DEVICE_ENTITIES = {"devices", "vm-users"}


def push_business_schemas(url: str, *, service_token: Optional[str] = None) -> None:
    """POST all entity schemas to Entangled's /v1/schema/register.

    Most action hook URLs point to BUSINESS_URL.
    Device entities (devices, vm-users) point directly to DEVICE_URL
    to avoid double-proxy (Business -> Device).
    """
    business_url = getattr(ServiceConfig, "BUSINESS_URL", "http://127.0.0.1:19998").rstrip("/")
    device_url = getattr(ServiceConfig, "DEVICE_URL", "http://127.0.0.1:19993").rstrip("/")

    specs = []
    for name, defn in ALL_BUSINESS_ENTITIES.items():
        spec = defn.to_spec()
        actions = ENTITY_ACTIONS.get(name, [])
        if actions:
            hook_base = device_url if name in _DEVICE_ENTITIES else business_url
            hooks = {}
            for action_name in actions:
                hooks[action_name] = f"{hook_base}/internal/entities/{name}/action/{action_name}"
            spec["action_hooks"] = hooks
        specs.append(spec)

    if not specs:
        logger.info("[BizSchemaPush] No entities to push.")
        return

    endpoint = f"{url.rstrip('/')}/v1/schema/register"
    payload = _json.dumps({"entities": specs}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if service_token:
        headers["X-Service-Token"] = service_token
        headers["X-User-ID"] = ""

    try:
        req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            result = _json.loads(body)
            registered = result.get("registered", [])
            errors = result.get("errors", [])
            logger.info(
                "[BizSchemaPush] Registered %d entities (%s); errors: %s",
                len(registered), endpoint, errors or "none",
            )
            if errors:
                for err in errors:
                    logger.error("[BizSchemaPush] Entity %s failed: %s", err.get("name"), err.get("error"))
    except Exception as exc:
        logger.error("[BizSchemaPush] Failed to push schemas: %s", exc)
