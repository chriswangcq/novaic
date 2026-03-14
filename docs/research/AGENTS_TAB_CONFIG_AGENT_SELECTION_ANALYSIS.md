# Agents Tab Config Agent Selection Flow — Analysis Report

> **Focus**: novaic-app — how `effectiveAgentId` flows from Layout/AgentDrawer to Settings, and correctness of agent selection logic.

---

## 1. Data Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  App.tsx                                                                         │
│  handleSelectAgent(agentId) → getAgentService().selectAgent(agentId)              │
│  → store.currentAgentId (sync update)                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LayoutContainer                                                                  │
│  handleSelectAgentForTools(agentId) → onSelectAgent(agentId) [from App]           │
│  handleSelectChat(agentId) → onSelectAgent(agentId)                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AgentDrawer                                                                      │
│  currentAgentId from useAgent() [store]                                           │
│  handleSelectAgentForTools(agent) → selectAgentForTools(agent.id)                 │
│  handleSelectChat(agent) → selectChat(agent.id)                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  SettingsModal → AgentToolsTab                                                    │
│  currentAgentId from useAgent() [store]                                           │
│  selectedAgentId from useState (dropdown)                                         │
│  effectiveAgentId = hideAgentSelector ? currentAgentId : selectedAgentId          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Where `currentAgentId` Comes From

| Source | Location | Description |
|--------|----------|-------------|
| **Store** | `useAppStore(s => s.currentAgentId)` | Global Zustand state |
| **Hook** | `useAgent()` → `currentAgentId` | Reads from store |
| **Setter** | `getAgentService().selectAgent(id)` | Calls `useAppStore.getState().setCurrentAgentId(id)` synchronously |

**Flow**: `AgentService.selectAgent(agentId)` (agentService.ts:101–112):

1. `setCurrentAgentId(agentId)` — **sync** store update
2. `prefsRepo.setSelectedAgent(...)` — async persist
3. `syncService.switchAgent(agentId)` — async
4. `modelService.loadForAgent(agentId)` — async

Store update is synchronous, so no race from delayed store propagation.

---

## 3. Where `selectedAgentId` Comes From

| Source | Location | Description |
|--------|----------|-------------|
| **Initial** | `useState<string>(currentAgentId || '')` | AgentToolsTab line 1569 |
| **User** | `<select onChange={e => setSelectedAgentId(e.target.value)}>` | Dropdown in AgentToolsTab (lines 1932–1941) |
| **Sync effect** | `useEffect` when `currentAgentId && !selectedAgentId` | Sets `selectedAgentId` from `currentAgentId` (lines 1793–1797) |

The dropdown is only shown when `!hideAgentSelector` (standalone Settings modal).

---

## 4. `effectiveAgentId` Logic

```ts
// SettingsModal.tsx:1570
const effectiveAgentId = hideAgentSelector ? (currentAgentId ?? '') : selectedAgentId;
```

| Mode | `hideAgentSelector` | `effectiveAgentId` | When |
|------|---------------------|--------------------|------|
| **Embedded** | `true` | `currentAgentId ?? ''` | Agents tab: AgentToolsTab in third column |
| **Standalone** | `false` | `selectedAgentId` | Settings modal (overlay) with dropdown |

```ts
// SettingsModal.tsx:2896
hideAgentSelector={embedded && embeddedMode === 'content' && embeddedTab === 'agent-tools'}
```

So `effectiveAgentId` is **not** `selectedAgentId || currentAgentId` in all cases:

- Embedded: `effectiveAgentId = currentAgentId` (no fallback to `selectedAgentId`)
- Standalone: `effectiveAgentId = selectedAgentId` (no fallback to `currentAgentId`)

---

## 5. Switching Agents — Does Config Load for the Right Agent?

### 5.1 Embedded (Agents tab)

1. User clicks agent B in drawer → `handleSelectAgentForTools(B)` → `onSelectAgent(B)` → `selectAgent(B)`
2. `currentAgentId` becomes B synchronously
3. AgentToolsTab re-renders with `effectiveAgentId = currentAgentId = B`
4. `loadData` depends on `effectiveAgentId` (line 1789)
5. `useEffect(() => loadData(), [loadData])` runs (line 1791)
6. Config loads for B

Correct.

### 5.2 Standalone (Settings modal)

1. User opens Settings from Header
2. AgentToolsTab shows dropdown; `effectiveAgentId = selectedAgentId`
3. User selects agent A from dropdown → `selectedAgentId = A` → `effectiveAgentId = A`
4. Config loads for A

Correct.

---

## 6. Potential Race / State Bugs

### 6.1 Stale load result when switching agents quickly

**Problem**: `loadData` is async and has no cancellation. If the user switches A → B → C quickly:

1. `loadData(A)` starts
2. User clicks B → `loadData(B)` starts
3. User clicks C → `loadData(C)` starts
4. Responses may finish in any order; the last one to finish wins

**Result**: UI can briefly show config for the wrong agent (e.g. B’s config while C is selected).

**Location**: `SettingsModal.tsx` lines 1687–1786.

**Fix**: Use a ref or cancellation flag:

```ts
const loadData = useCallback(async () => {
  if (!effectiveAgentId) return;
  const loadId = effectiveAgentId;
  setLoading(true);
  // ...
  try {
    const [/* ... */] = await Promise.allSettled([/* ... */]);
    if (loadId !== effectiveAgentId) return; // Ignore stale result
    setCategories(/* ... */);
    // ...
  } finally {
    if (loadId === effectiveAgentId) setLoading(false);
  }
}, [/* ... */]);
```

Or use `AbortController` if the API supports it.

---

### 6.2 `selectedAgentId` not synced when `currentAgentId` changes (embedded)

**Sync effect** (lines 1793–1797):

```ts
useEffect(() => {
  if (currentAgentId && !selectedAgentId) {
    setSelectedAgentId(currentAgentId);
  }
}, [currentAgentId, selectedAgentId]);
```

When embedded, `effectiveAgentId = currentAgentId`, so `selectedAgentId` is not used for display. The effect only runs when `!selectedAgentId`, so `selectedAgentId` can stay stale after switching agents. This does not affect correctness because `effectiveAgentId` ignores it in embedded mode.

**Verdict**: No functional bug; only local state is slightly out of sync.

---

### 6.3 Initial `selectedAgentId` when `currentAgentId` is null

```ts
const [selectedAgentId, setSelectedAgentId] = useState<string>(currentAgentId || '');
```

On first render, if `currentAgentId` is null, `selectedAgentId = ''`. The sync effect will set it when `currentAgentId` becomes non-null. In standalone mode, `effectiveAgentId = ''` until the user picks from the dropdown, which is correct.

**Verdict**: Correct.

---

### 6.4 `loadSubjectsForDevice` inside `loadData` — nested async

`loadData` awaits `loadSubjectsForDevice` (lines 1739–1745). If the user switches agents before that finishes, the same stale-result issue applies. The suggested `loadId` check would cover this as well.

---

## 7. Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| `currentAgentId` source | OK | Store via `useAgent()`, updated by `selectAgent()` |
| `selectedAgentId` source | OK | `useState` + dropdown + sync effect |
| `effectiveAgentId` logic | OK | Correct split between embedded and standalone |
| Config load on agent switch | OK | `loadData` re-runs when `effectiveAgentId` changes |
| Race: fast agent switching | Bug | Stale async results can overwrite UI |
| Sync effect semantics | OK | Only used when dropdown is shown |

---

## 8. Recommendations

1. Add a `loadId` (or similar) guard in `loadData` to ignore results from outdated agent IDs.
2. Optionally sync `selectedAgentId` with `currentAgentId` when embedded, for consistency (e.g. when switching to standalone later).
3. Consider `AbortController` for API calls if supported, for cleaner cancellation.
