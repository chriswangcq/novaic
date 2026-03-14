# Agent Tools Tab Config — Correctness Analysis

**Scope:** `novaic-app/src/components/Settings/SettingsModal.tsx` — `AgentToolsTab` and related config panels.

---

## 1. effectiveAgentId Determination

```tsx
const [selectedAgentId, setSelectedAgentId] = useState<string>(currentAgentId || '');
const effectiveAgentId = hideAgentSelector ? (currentAgentId ?? '') : selectedAgentId;
```

| Mode | effectiveAgentId | Source |
|------|------------------|--------|
| **Normal** (agent selector visible) | `selectedAgentId` | User selection in dropdown |
| **Embedded** (`hideAgentSelector=true`) | `currentAgentId ?? ''` | Current agent from `useAgent()` |

**Sync effect:**
```tsx
useEffect(() => {
  if (currentAgentId && !selectedAgentId) {
    setSelectedAgentId(currentAgentId);
  }
}, [currentAgentId, selectedAgentId]);
```

- When `currentAgentId` becomes available and `selectedAgentId` is empty, it syncs.
- When the user changes agent in the main UI, `selectedAgentId` is not auto-updated (user keeps editing the agent they chose in Settings).

**Verdict:** Correct. Normal mode uses explicit selection; embedded mode uses current agent.

---

## 2. loadData — APIs and Order

| Order | API | Source | Purpose |
|-------|-----|--------|---------|
| 0 | `getModelService().loadConfig()` | ModelService | Load app config (API keys, candidate models) |
| 1 | `settings.getToolCategories()` | api | Tool categories (global) |
| 2 | `settings.getAgentToolsConfig(effectiveAgentId)` | api | `disabled_tools`, `custom_instructions` |
| 3 | `settings.getSkills(true)` | api | All skills (global) |
| 4 | `settings.getAgentSkills(effectiveAgentId)` | api | Assigned skill IDs for agent |
| 5 | `api.devices.listForUser()` | api | User devices |
| 6 | `api.getAgentBinding(effectiveAgentId)` | api | Device binding |
| 7 | `api.getAgentModel(effectiveAgentId)` | api | Agent model config |

**Parallel:** 2–7 run via `Promise.allSettled`.

**Sequential after parallel:**
- `settings.getPromptsPreview(effectiveAgentId)` — prompts preview
- `settings.getBootstrapFiles(effectiveAgentId)` — soul_md, heartbeat_md, memory_md, user_md, active_hours_*

**Sequential (conditional):**
- If binding has `device_id`: `loadSubjectsForDevice(binding.device_id, { subjectType, subjectId, mountedTools })` — device subjects and mounted tools.

**Verdict:** Order is correct. All agent-scoped calls use `effectiveAgentId`.

---

## 3. handleSave — APIs and Payloads

| API | Payload | Notes |
|-----|---------|-------|
| `settings.saveAgentToolsConfig(effectiveAgentId, {...})` | `{ disabled_tools, custom_instructions }` | Matches backend `UpdateToolsConfigRequest` |
| `settings.setAgentSkills(effectiveAgentId, assignedSkillIds)` | `skillIds: string[]` | Backend expects `{ skill_ids: skillIds }` |
| `settings.saveBootstrapFiles(effectiveAgentId, {...})` | `{ soul_md, heartbeat_md, active_hours_start, active_hours_end, active_hours_timezone }` | memory_md, user_md intentionally omitted (Agent-maintained) |
| `api.setAgentBinding(effectiveAgentId, {...})` | `{ device_id, subject_type, subject_id, mounted_tools }` | When `bindingDeviceId && selectedSubjectType` |
| `api.clearAgentBinding(effectiveAgentId)` | — | When `currentBinding` exists but no new binding |

**Model:** Not saved in `handleSave`. Saved via `getModelService().setModel(effectiveAgentId, v)` on change. Intentional.

**Verdict:** Payloads and conditions are correct.

---

## 4. Field-by-Field Consistency

| Field | Load | Save | UI |
|-------|------|------|-----|
| `disabled_tools` | ✅ | ✅ | ✅ |
| `custom_instructions` | ✅ | ✅ | ✅ |
| `soul_md` | ✅ | ✅ | Editable |
| `heartbeat_md` | ✅ | ✅ | Editable |
| `memory_md` | ✅ | ❌ | Read-only |
| `user_md` | ✅ | ❌ | Read-only |
| `active_hours_*` | ✅ | ✅ | ✅ |
| `binding` | ✅ | ✅ (set/clear) | ✅ |
| `model` | ✅ | ✅ (on change) | ✅ |
| `assignedSkills` | ✅ | ✅ | ✅ |

**Verdict:** Load/save/UI alignment is correct.

---

## 5. Data Flow & Agent Scoping

| Concern | Status |
|--------|--------|
| All agent-scoped APIs use `effectiveAgentId` | ✅ |
| `loadData` runs when `effectiveAgentId` changes | ✅ |
| Loading state shows while fetching | ✅ |
| `loadData` deps: `[loadSubjectsForDevice, effectiveAgentId]` | ✅ (settings excluded to avoid infinite loop) |

---

## 6. Issues & Recommendations

### 6.1 Model API: api_key_id Not Sent

**Problem:** `ModelService.setModel` receives composite `api_key_id:model_id` but only sends `model_id` to `api.setAgentModel`. The backend `SetAgentModelRequest` only has `model_id`. The `candidate_models` table uses `(id, api_key_id)` as primary key, so the same `model_id` can exist under different API keys. The backend lookup `WHERE m.id = ? AND k.user_id = ? LIMIT 1` can return an arbitrary row when multiple keys share the same model id.

**Recommendation:** Extend the backend to accept `api_key_id` and use it in the lookup, or ensure model ids are unique per user.

### 6.2 Binding Save When Subject Not Selected

**Logic:**
```tsx
if (bindingDeviceId && selectedSubjectType) {
  saveTasks.push(api.setAgentBinding(...));
} else if (currentBinding) {
  saveTasks.push(api.clearAgentBinding(...));
}
```

If the user selects a device but `loadSubjectsForDevice` fails, `selectedSubjectType` stays empty and neither set nor clear runs. The old binding remains.

**Recommendation:** Either require a subject before saving a new binding, or show a clear error when subjects fail to load.

### 6.3 useSettings() Creates New Object Each Render

The comment notes that `settings` from `useSettings()` is a new object each render, so it is excluded from `loadData` deps to avoid infinite re-runs. This is correct; `useSettings()` returns a fresh object each time.

---

## 7. Summary

| Aspect | Correctness |
|--------|-------------|
| effectiveAgentId (current vs selected) | ✅ Correct |
| loadData API order and scoping | ✅ Correct |
| handleSave APIs and payloads | ✅ Correct |
| disabled_tools, custom_instructions | ✅ Consistent |
| Bootstrap files (soul, heartbeat, active_hours) | ✅ Consistent |
| memory_md, user_md (read-only) | ✅ Intentional |
| Binding (set/clear) | ✅ Correct |
| Model (on-change save) | ⚠️ api_key_id not sent |
| Save/load consistency | ✅ Aligned |
