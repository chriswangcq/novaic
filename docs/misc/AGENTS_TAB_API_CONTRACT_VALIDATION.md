# Agents Tab API Contract Validation Report

Validation of request/response contracts between frontend (`novaic-app`) and Gateway (`novaic-gateway`) for the agents tab config.

---

## 1. Tools Config

| Aspect | Frontend | Gateway | Status |
|--------|----------|---------|--------|
| **GET** path | `/api/agents/{id}/tools-config` | `/api/agents/{agent_id}/tools-config` | ✅ Match |
| **GET** response | expects `{ disabled_tools, custom_instructions }` | returns `{ agent_id, disabled_tools, custom_instructions }` | ✅ Match (extra `agent_id` OK) |
| **POST** path | `/api/agents/{id}/tools-config` | `/api/agents/{agent_id}/tools-config` | ✅ Match |
| **POST** body | `{ disabled_tools?, custom_instructions? }` | `ToolsConfigRequest`: `disabled_tools?: List[str]`, `custom_instructions?: str` | ✅ Match |
| **POST** response | `any` (not typed) | `{ success: true, agent_id }` | ✅ Match |
| **404** | Uses `Promise.allSettled`; treats rejection as load error | `check_agent_access` → 404 if agent not found | ✅ Handled |

**Note:** Both `agents.py` and `skills.py` define tools-config routes. `agents_router` is mounted first, so `agents.py` handles the request. Both use `DriveRepository` with same logic.

---

## 2. Bootstrap Files

| Aspect | Frontend | Gateway | Status |
|--------|----------|---------|--------|
| **GET** path | `/api/agents/{id}/bootstrap-files` | `/api/agents/{agent_id}/bootstrap-files` | ✅ Match |
| **GET** response | `{ soul_md, heartbeat_md, memory_md, user_md, active_hours_start, active_hours_end, active_hours_timezone }` | Same fields (snake_case) | ✅ Match |
| **POST** path | `/api/agents/{id}/bootstrap-files` | `/api/agents/{agent_id}/bootstrap-files` | ✅ Match |
| **POST** body | `{ soul_md?, heartbeat_md?, memory_md?, user_md?, active_hours_start?, active_hours_end?, active_hours_timezone? }` | `data.get("soul_md")` etc. — all optional | ✅ Match |
| **POST** response | `{ success: boolean }` | `{ success, agent_id }` or `{ success, agent_id, skipped }` or `{ success, agent_id, no_changes }` or `{ success: false, agent_id, error }` | ✅ Match (frontend only needs `success`) |
| **404** | try/catch → setLoadError | `check_agent_access` → 404 | ✅ Handled |

---

## 3. Skills

| Aspect | Frontend | Gateway | Status |
|--------|----------|---------|--------|
| **GET** path | `/api/agents/{id}/skills` | `/api/agents/{agent_id}/skills` | ✅ Match |
| **GET** response | `{ skills: any[], count: number }` | `{ skills, count }` | ✅ Match |
| **POST** path | `/api/agents/{id}/skills` | `/api/agents/{agent_id}/skills` | ✅ Match |
| **POST** body | `{ skill_ids: string[] }` | `data.get("skill_ids", [])` | ✅ Match |
| **POST** response | `any` | `{ success: true, count: number }` | ✅ Match |
| **404** | Promise.allSettled | `check_agent_access` → 404 | ✅ Handled |

**Frontend usage:** `setAssignedSkillIds(((agentSkillsRes?.skills) || []).map((s: any) => s.id))` — expects each skill to have `id`. Gateway `get_agent_skills` returns skill objects with `id` from `_row_to_dict` or builtin skill dict. ✅

---

## 4. Binding

| Aspect | Frontend | Gateway | Status |
|--------|----------|---------|--------|
| **GET** path | `/api/agents/{id}/binding` | `/api/agents/{agent_id}/binding` | ✅ Match |
| **GET** response | `AgentDeviceBinding \| null` | `AgentDeviceBindingResponse` or `None` (204/200 with null body) | ⚠️ See note |
| **PUT** path | `/api/agents/{id}/binding` | `/api/agents/{agent_id}/binding` | ✅ Match |
| **PUT** body | `UpsertAgentDeviceBindingRequest`: `device_id`, `subject_type`, `subject_id?`, `mounted_tools?` | `UpsertAgentDeviceBindingRequest`: same (snake_case) | ✅ Match |
| **PUT** response | `AgentDeviceBinding` | `AgentDeviceBindingResponse` | ✅ Match |
| **DELETE** path | `/api/agents/{id}/binding` | `/api/agents/{agent_id}/binding` | ✅ Match |
| **DELETE** response | `void` | 204 No Content | ✅ Match |
| **404** | — | `check_agent_access` → 404; Device not found → 404 | ✅ Handled |

**Field names (Binding response):** All snake_case on both sides: `agent_id`, `device_id`, `subject_type`, `subject_id`, `mounted_tools`, `created_at`, `updated_at`, `device_type`, `device_name`, `subject_label`, `desktop_resource_id`, `supported_tools`. ✅

**GET binding when no binding:** Gateway returns `None` (Python) → FastAPI serializes as `null` in JSON. Frontend expects `AgentDeviceBinding | null`. ✅

---

## 5. Model

| Aspect | Frontend | Gateway | Status |
|--------|----------|---------|--------|
| **GET** path | `/api/agents/{id}/model` | `/api/agents/{agent_id}/model` | ✅ Match |
| **GET** response | `AgentModelConfig`: `{ agent_id, model_id, model, api_key?, api_base? }` | `AgentModelConfigResponse`: `{ agent_id, model_id, model, api_key?, api_base? }` | ✅ Match |
| **PUT** path | `/api/agents/{id}/model` | `/api/agents/{agent_id}/model` | ✅ Match |
| **PUT** body | `{ model_id: string }` | `SetAgentModelRequest`: `model_id: str` (required) | ✅ Match |
| **PUT** response | `void` (not used) | `{ success, agent_id, model_id, provider_name }` | ✅ OK (frontend ignores) |
| **404** | — | `check_agent_access` → 404 | ✅ Handled |

**Mismatch:** Frontend `AgentModelConfig.model_id` is typed as `string | null`, but Gateway can return `model_id: null` when no model is set. ✅ Compatible.

---

## 6. Summary of Mismatches

### No Critical Mismatches

All contracts align. Minor notes:

| Category | Finding |
|----------|---------|
| **Field names** | All use snake_case consistently. No camelCase/snake_case mismatch. |
| **Required vs optional** | Tools config POST: both optional. Bootstrap POST: all optional. Skills POST: `skill_ids` required (empty array OK). Binding PUT: `device_id`, `subject_type` required; `subject_id`, `mounted_tools` optional. Model PUT: `model_id` required. |
| **404 handling** | All agent-scoped endpoints use `check_agent_access` → 404 "Agent not found". Frontend uses `Promise.allSettled` for parallel loads and surfaces errors. |
| **Duplicate routes** | `tools-config` exists in both `agents.py` and `skills.py`. `agents_router` is mounted first, so `agents.py` handles it. Consider removing from `skills.py` to avoid confusion. |

### Optional Improvements

1. **Tools config POST response:** Frontend `saveAgentToolsConfig` returns `any`. Gateway returns `{ success, agent_id }`. Consider typing the response.
2. **Skills POST response:** Frontend `setAgentSkills` returns `any`. Gateway returns `{ success, count }`. Consider typing.
3. **Bootstrap POST:** Frontend sends `soul_md`, `heartbeat_md`, `memory_md`, `user_md` in save (SettingsModal sends `soul_md`, `heartbeat_md` but comment says "memory_md 和 user_md 是 Agent 维护的"). Gateway accepts all. No mismatch.
4. **Agent not found:** When agent is deleted mid-session, subsequent API calls return 404. Frontend catches and shows error. No change needed.

---

## 7. Route Registration Order

```
main_gateway.py:
  app.include_router(api_router, prefix="/api")      # /api/*
  app.include_router(agents_router)                  # /api/agents/* (prefix in router)
  app.include_router(skills_router)                   # /api/* (skills has /agents/{id}/...)
```

Both `agents.py` and `skills.py` define `/agents/{agent_id}/tools-config`. First match wins → `agents.py` handles it.

---

## 8. API Endpoint Summary

| Endpoint | Handler | Frontend Call |
|----------|---------|---------------|
| GET `/api/agents/{id}/tools-config` | agents.py | `getAgentToolsConfig` |
| POST `/api/agents/{id}/tools-config` | agents.py | `saveAgentToolsConfig` |
| GET `/api/agents/{id}/bootstrap-files` | skills.py | `getBootstrapFiles` |
| POST `/api/agents/{id}/bootstrap-files` | skills.py | `saveBootstrapFiles` |
| GET `/api/agents/{id}/skills` | skills.py | `getAgentSkills` |
| POST `/api/agents/{id}/skills` | skills.py | `setAgentSkills` |
| GET `/api/agents/{id}/binding` | agents.py | `getAgentBinding` |
| PUT `/api/agents/{id}/binding` | agents.py | `setAgentBinding` |
| DELETE `/api/agents/{id}/binding` | agents.py | `clearAgentBinding` |
| GET `/api/agents/{id}/model` | agents.py | `getAgentModel` |
| PUT `/api/agents/{id}/model` | agents.py | `setAgentModel` |
