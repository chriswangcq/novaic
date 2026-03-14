# Agents Tab Config API Correctness Analysis

**Focus:** `novaic-app/src/services/api.ts` and settings-related code  
**Date:** 2025-03-13

---

## Summary

All agent config API calls in the frontend match backend paths, methods, and body shapes. No typos or wrong paths found. One minor type mismatch: `saveBootstrapFiles` backend can return extra fields (`agent_id`, `skipped`, `no_changes`, `error`) beyond `{ success: boolean }`, but the frontend does not rely on them.

---

## 1. getAgentToolsConfig / saveAgentToolsConfig

| API | Path | Method | Body | Backend | Status |
|-----|------|--------|------|---------|--------|
| getAgentToolsConfig | `GET /api/agents/{agentId}/tools-config` | GET | — | `agents.py` L469, `skills.py` L234 (duplicate) | ✓ |
| saveAgentToolsConfig | `POST /api/agents/{agentId}/tools-config` | POST | `{ disabled_tools?, custom_instructions? }` | `agents.py` L485, `skills.py` L260 (duplicate) | ✓ |

**Frontend (api.ts L666-672):**
```ts
getAgentToolsConfig:  gateway_get  → /api/agents/${agentId}/tools-config
saveAgentToolsConfig: gateway_post → /api/agents/${agentId}/tools-config, body: data
```

**Backend:** `ToolsConfigRequest` expects `disabled_tools: List[str]`, `custom_instructions: str`.

**Expected response (GET):**
```json
{
  "agent_id": string,
  "disabled_tools": string[],
  "custom_instructions": string
}
```

**Expected response (POST):**
```json
{ "success": true, "agent_id": string }
```

**Note:** Both `agents.py` and `skills.py` define these routes. `agents_router` is mounted before `skills_router`, so `agents.py` handles the request. The duplicate in `skills.py` is dead code.

---

## 2. getAgentSkills / setAgentSkills

| API | Path | Method | Body | Backend | Status |
|-----|------|--------|------|---------|--------|
| getAgentSkills | `GET /api/agents/{agentId}/skills` | GET | — | `skills.py` L207 | ✓ |
| setAgentSkills | `POST /api/agents/{agentId}/skills` | POST | `{ skill_ids: string[] }` | `skills.py` L219 | ✓ |

**Frontend (api.ts L654-660):**
```ts
getAgentSkills: gateway_get  → /api/agents/${agentId}/skills
setAgentSkills: gateway_post → /api/agents/${agentId}/skills, body: { skill_ids: skillIds }
```

**Expected response (GET):**
```json
{ "skills": Array<{ id: string; ... }>, "count": number }
```

**Expected response (POST):**
```json
{ "success": true, "count": number }
```

**SettingsModal usage:** `(agentSkillsRes?.skills || []).map((s: any) => s.id)` — expects each skill to have `id`. Backend `get_agent_skills` returns skills with `id` (builtin: `builtin:xxx`, custom: DB id). ✓

---

## 3. getAgentBinding / setAgentBinding / clearAgentBinding

| API | Path | Method | Body | Backend | Status |
|-----|------|--------|------|---------|--------|
| getAgentBinding | `GET /api/agents/{agentId}/binding` | GET | — | `agents.py` L408 | ✓ |
| setAgentBinding | `PUT /api/agents/{agentId}/binding` | PUT | `UpsertAgentDeviceBindingRequest` | `agents.py` L505 | ✓ |
| clearAgentBinding | `DELETE /api/agents/{agentId}/binding` | DELETE | — | `agents.py` L575 | ✓ |

**Frontend (api.ts L506-524):**
```ts
getAgentBinding:  gateway_get    → /api/agents/${agentId}/binding
setAgentBinding: gateway_put    → /api/agents/${agentId}/binding, body: data
clearAgentBinding: gateway_delete → /api/agents/${agentId}/binding
```

**Body for setAgentBinding:**
```ts
{ device_id: string; subject_type: DeviceSubjectType; subject_id?: string; mounted_tools?: MountedToolsByCategory }
```

**Expected response (GET):** `AgentDeviceBinding | null`  
**Expected response (PUT):** `AgentDeviceBinding`  
**Expected response (DELETE):** 204 No Content

---

## 4. getAgentModel / setAgentModel

| API | Path | Method | Body | Backend | Status |
|-----|------|--------|------|---------|--------|
| getAgentModel | `GET /api/agents/{agentId}/model` | GET | — | `agents.py` L519 | ✓ |
| setAgentModel | `PUT /api/agents/{agentId}/model` | PUT | `{ model_id: string }` | `agents.py` L586 | ✓ |

**Frontend (api.ts L432-441):**
```ts
getAgentModel: gateway_get → /api/agents/${agentId}/model
setAgentModel: gateway_put → /api/agents/${agentId}/model, body: { model_id: modelId }
```

**Expected response (GET):**
```json
{
  "agent_id": string,
  "model_id": string | null,
  "model": CandidateModel | null,
  "api_key"?: string,
  "api_base"?: string
}
```

**Expected response (PUT):**
```json
{ "success": true, "agent_id": string, "model_id": string, "provider_name": string }
```

---

## 5. getBootstrapFiles / saveBootstrapFiles

| API | Path | Method | Body | Backend | Status |
|-----|------|--------|------|---------|--------|
| getBootstrapFiles | `GET /api/agents/{agentId}/bootstrap-files` | GET | — | `skills.py` L364 | ✓ |
| saveBootstrapFiles | `POST /api/agents/{agentId}/bootstrap-files` | POST | Partial bootstrap fields | `skills.py` L395 | ✓ |

**Frontend (api.ts L636-664):**
```ts
getBootstrapFiles:  gateway_get  → /api/agents/${agentId}/bootstrap-files
saveBootstrapFiles: gateway_post → /api/agents/${agentId}/bootstrap-files, body: data
```

**Expected response (GET):**
```json
{
  "soul_md": string,
  "heartbeat_md": string,
  "memory_md": string,
  "user_md": string,
  "active_hours_start": string,
  "active_hours_end": string,
  "active_hours_timezone": string
}
```

**Expected response (POST):**
```json
{ "success": boolean, "agent_id"?: string, "skipped"?: boolean, "no_changes"?: boolean, "error"?: string }
```

**SettingsModal:** Sends `soul_md`, `heartbeat_md`, `active_hours_start`, `active_hours_end`, `active_hours_timezone` (does not send `memory_md`/`user_md` per design). ✓

---

## 6. getPromptsPreview

| API | Path | Method | Body | Backend | Status |
|-----|------|--------|------|---------|--------|
| getPromptsPreview | `GET /api/agents/{agentId}/prompts-preview` | GET | — | `skills.py` L300 | ✓ |

**Frontend (api.ts L674-676):**
```ts
getPromptsPreview: gateway_get → /api/agents/${agentId}/prompts-preview
```

**Expected response:**
```json
{
  "agent_id": string,
  "system_prompt": string,
  "system_prompt_length": number,
  "wake_message": string,
  "wake_message_length": number,
  "note"?: string
}
```

---

## 7. getToolCategories

| API | Path | Method | Body | Backend | Status |
|-----|------|--------|------|---------|--------|
| getToolCategories | `GET /api/tools/categories` | GET | — | `skills.py` L345 | ✓ |

**Frontend (api.ts L678-680):**
```ts
getToolCategories: gateway_get → /api/tools/categories
```

**Expected response:**
```json
{
  "categories": Record<string, {
    "name": string,
    "count": number,
    "tools": Array<{ "name": string, "description": string }>
  }>
}
```

**SettingsModal:** Uses `catRes?.categories` ✓

---

## 8. useSettings Bridge

`useSettings()` in `novaic-app/src/components/hooks/useSettings.ts` forwards to `api`:

- `getToolCategories` → `api.getToolCategories()`
- `getAgentToolsConfig` → `api.getAgentToolsConfig(agentId)`
- `saveAgentToolsConfig` → `api.saveAgentToolsConfig(agentId, data)`
- `getAgentSkills` → `api.getAgentSkills(agentId)`
- `setAgentSkills` → `api.setAgentSkills(agentId, skillIds)`
- `getPromptsPreview` → `api.getPromptsPreview(agentId)`
- `getBootstrapFiles` → `api.getBootstrapFiles(agentId)`
- `saveBootstrapFiles` → `api.saveBootstrapFiles(agentId, data)`

Binding and model APIs are called directly from `api` in SettingsModal (not via useSettings).

---

## 9. Findings

| Finding | Severity |
|---------|----------|
| All paths, methods, and body shapes match backend | — |
| No typos or wrong paths | — |
| Duplicate `tools-config` routes in `agents.py` and `skills.py`; `agents.py` wins | Low (dead code in skills.py) |
| `saveBootstrapFiles` return type in frontend is `{ success: boolean }`; backend can add `agent_id`, `skipped`, `no_changes`, `error` | Low (frontend ignores extra fields) |

---

## 10. Recommendation

- Consider removing the duplicate `tools-config` routes from `skills.py` to avoid confusion.
- Optionally extend the frontend `saveBootstrapFiles` return type to include `agent_id`, `skipped`, `no_changes`, `error` for consistency and future use.
