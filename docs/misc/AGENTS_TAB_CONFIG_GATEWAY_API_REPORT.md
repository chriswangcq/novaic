# Agents Tab Config — Gateway API Correctness Report

**Focus:** `novaic-gateway/gateway/api/agents.py` and related agent config endpoints  
**Date:** 2025-03-13

---

## 1. Executive Summary

Agent-related config endpoints are split across **two routers**:
- **`agents.py`** (prefix `/api/agents`): tools-config, binding, model, models/available
- **`skills.py`** (prefix `/api`): tools-config (duplicate), skills, prompts-preview, bootstrap-files

All frontend-called endpoints exist. **tools-config** is duplicated; **skills**, **bootstrap-files**, and **prompts-preview** live only in `skills.py`. Route registration order determines which tools-config handler is used.

---

## 2. Endpoint Table

### 2.1 Tools Config

| Endpoint | Method | Gateway Location | check_agent_access | Request Schema | Response Schema | Frontend Call |
|----------|--------|------------------|--------------------|----------------|-----------------|---------------|
| `/api/agents/{agent_id}/tools-config` | GET | agents.py L410 | ✅ | — | `{agent_id, disabled_tools[], custom_instructions}` | `api.getAgentToolsConfig(agentId)` → GET ✅ |
| `/api/agents/{agent_id}/tools-config` | POST | agents.py L419 | ✅ | `ToolsConfigRequest`: `{disabled_tools?, custom_instructions?}` | `{success, agent_id}` | `api.saveAgentToolsConfig(agentId, data)` → POST ✅ |
| `/api/agents/{agent_id}/tools-config` | GET | skills.py L234 | ✅ | — | same | **Duplicate** |
| `/api/agents/{agent_id}/tools-config` | POST | skills.py L259 | ✅ | `Dict[str, Any]` (loose) | same | **Duplicate** |

**Findings:**
- Path and method match frontend.
- Body shape: frontend sends `{ disabled_tools?, custom_instructions? }`; both backends accept it.
- **Duplicate routes:** agents.py and skills.py both define GET/POST. `agents_router` is registered first → agents.py handlers win.

---

### 2.2 Binding

| Endpoint | Method | Gateway Location | check_agent_access | Request Schema | Response Schema | Frontend Call |
|----------|--------|------------------|--------------------|----------------|----------------|---------------|
| `/api/agents/{agent_id}/binding` | GET | agents.py L403 | ✅ | — | `AgentDeviceBindingResponse` or null | `api.getAgentBinding(agentId)` → GET ✅ |
| `/api/agents/{agent_id}/binding` | PUT | agents.py L424 | ✅ | `UpsertAgentDeviceBindingRequest`: `{device_id, subject_type, subject_id?, mounted_tools?}` | `AgentDeviceBindingResponse` | `api.setAgentBinding(agentId, data)` → PUT ✅ |
| `/api/agents/{agent_id}/binding` | DELETE | agents.py L451 | ✅ | — | 204 No Content | `api.clearAgentBinding(agentId)` → DELETE ✅ |

**Findings:**
- Path, method, and schema match frontend.
- `UpsertAgentDeviceBindingRequest` aligns with `api.ts` `UpsertAgentDeviceBindingRequest`.

---

### 2.3 Model

| Endpoint | Method | Gateway Location | check_agent_access | Request Schema | Response Schema | Frontend Call |
|----------|--------|------------------|--------------------|----------------|----------------|---------------|
| `/api/agents/models/available` | GET | agents.py L521 | N/A (user-scoped) | — | `List[CandidateModelResponse]` | `api.listAvailableModels()` → GET ✅ |
| `/api/agents/{agent_id}/model` | GET | agents.py L531 | ✅ | — | `AgentModelConfigResponse` | `api.getAgentModel(agentId)` → GET ✅ |
| `/api/agents/{agent_id}/model` | PUT | agents.py L608 | ✅ | `SetAgentModelRequest`: `{model_id}` | `{success, agent_id, model_id, provider_name}` | `api.setAgentModel(agentId, modelId)` → PUT ✅ |

**Findings:**
- Paths and methods match.
- Frontend sends `{ model_id: string }`; backend expects `SetAgentModelRequest.model_id`.
- `AgentModelConfigResponse` matches `AgentModelConfig` in api.ts.

---

### 2.4 Skills

| Endpoint | Method | Gateway Location | check_agent_access | Request Schema | Response Schema | Frontend Call |
|----------|--------|------------------|--------------------|----------------|----------------|---------------|
| `/api/agents/{agent_id}/skills` | GET | skills.py L206 | ✅ | — | `{skills[], count}` | `api.getAgentSkills(agentId)` → GET ✅ |
| `/api/agents/{agent_id}/skills` | POST | skills.py L218 | ✅ | `{skill_ids: string[]}` | repo return | `api.setAgentSkills(agentId, skillIds)` → POST ✅ |

**Findings:**
- Endpoints exist only in **skills.py**, not in agents.py.
- Path and method match.
- Frontend sends `{ skill_ids: skillIds }`; backend expects `skill_ids`.

---

### 2.5 Bootstrap Files

| Endpoint | Method | Gateway Location | check_agent_access | Request Schema | Response Schema | Frontend Call |
|----------|--------|------------------|--------------------|----------------|----------------|---------------|
| `/api/agents/{agent_id}/bootstrap-files` | GET | skills.py L363 | ✅ | — | `{soul_md, heartbeat_md, memory_md, user_md, active_hours_*}` | `api.getBootstrapFiles(agentId)` → GET ✅ |
| `/api/agents/{agent_id}/bootstrap-files` | POST | skills.py L393 | ✅ | `{soul_md?, heartbeat_md?, memory_md?, user_md?, active_hours_*?}` | `{success}` | `api.saveBootstrapFiles(agentId, data)` → POST ✅ |

**Findings:**
- Endpoints exist only in **skills.py**.
- Path and method match.
- Response fields match frontend types.

---

### 2.6 Prompts Preview

| Endpoint | Method | Gateway Location | check_agent_access | Request Schema | Response Schema | Frontend Call |
|----------|--------|------------------|--------------------|----------------|----------------|---------------|
| `/api/agents/{agent_id}/prompts-preview` | GET | skills.py L299 | ✅ | — | `{agent_id, system_prompt, system_prompt_length, wake_message, wake_message_length}` | `api.getPromptsPreview(agentId)` → GET ✅ |

**Findings:**
- Endpoint exists only in **skills.py**.
- Path and method match.

---

## 3. Router Registration Order

```python
# main_gateway.py
app.include_router(api_router, prefix="/api")
app.include_router(agents_router)           # prefix="/api/agents"
app.include_router(skills_router)           # prefix="/api"
```

- **agents_router** defines `/{agent_id}/tools-config` → full path `/api/agents/{agent_id}/tools-config`.
- **skills_router** defines `/agents/{agent_id}/tools-config` → full path `/api/agents/{agent_id}/tools-config`.

First registered route wins → **agents.py** tools-config handlers are used.

---

## 4. Findings Summary

| Category | Status | Notes |
|----------|--------|-------|
| **tools-config** | ✅ Exists, ⚠️ Duplicate | Implemented in agents.py and skills.py; agents.py wins |
| **binding** | ✅ Correct | agents.py only; path/method/schema match |
| **model** | ✅ Correct | agents.py only |
| **skills** | ✅ Correct | skills.py only |
| **bootstrap-files** | ✅ Correct | skills.py only |
| **prompts-preview** | ✅ Correct | skills.py only |

---

## 5. Recommendations

1. **Remove duplicate tools-config from skills.py**  
   Keep a single implementation in agents.py (or skills.py) to avoid confusion and routing ambiguity.

2. **Add missing `ServiceConfig` import in agents.py**  
   Lines 693 and 709 use `ServiceConfig.TOOLS_SERVER_URL` in MCP endpoints without importing `ServiceConfig`; this will raise `NameError` if those routes are called.

3. **Optional: Consolidate agent config endpoints**  
   Consider moving skills, bootstrap-files, and prompts-preview into agents.py for a single place for agent config, or document the split clearly.

---

## 6. Frontend API Call Reference

| Frontend Method | Path | Method | Body |
|----------------|------|--------|------|
| `getAgentToolsConfig` | `/api/agents/{id}/tools-config` | GET | — |
| `saveAgentToolsConfig` | `/api/agents/{id}/tools-config` | POST | `{disabled_tools?, custom_instructions?}` |
| `getAgentBinding` | `/api/agents/{id}/binding` | GET | — |
| `setAgentBinding` | `/api/agents/{id}/binding` | PUT | `UpsertAgentDeviceBindingRequest` |
| `clearAgentBinding` | `/api/agents/{id}/binding` | DELETE | — |
| `listAvailableModels` | `/api/agents/models/available` | GET | — |
| `getAgentModel` | `/api/agents/{id}/model` | GET | — |
| `setAgentModel` | `/api/agents/{id}/model` | PUT | `{model_id}` |
| `getAgentSkills` | `/api/agents/{id}/skills` | GET | — |
| `setAgentSkills` | `/api/agents/{id}/skills` | POST | `{skill_ids: string[]}` |
| `getBootstrapFiles` | `/api/agents/{id}/bootstrap-files` | GET | — |
| `saveBootstrapFiles` | `/api/agents/{id}/bootstrap-files` | POST | Partial bootstrap fields |
| `getPromptsPreview` | `/api/agents/{id}/prompts-preview` | GET | — |
