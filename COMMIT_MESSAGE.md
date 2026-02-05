# Commit Message

## Summary

Major refactor: macOS path fixes, frontend chat improvements, backend enum standardization, and v24 runtime summary features

## Changes Overview

- **106 files changed**: 3,426 insertions(+), 2,035 deletions(-)

## Key Changes

### 1. macOS Cross-Platform Path Fixes
- Fixed 23 hardcoded paths across Python, Rust, and Shell scripts
- Implemented cross-platform data directory detection (macOS/Linux/Windows)
- Updated VM manager, SSH, setup scripts to use `tempfile.gettempdir()`
- Fixed QEMU socket paths to use platform-agnostic temporary directories
- Updated test scripts to use relative paths or `Path.home()`

**Files**: 
- `novaic-backend/gateway/vm/manager.py`
- `novaic-backend/gateway/vm/ssh.py`
- `novaic-backend/gateway/vm/setup.py`
- `scripts/release-vm-disk-lock.sh`
- `novaic-backend/run_gateways.sh`
- `novaic-vm/src/novaic_mcp_vmuse/config.py`
- `novaic-vm/src/novaic_mcp_vmuse/tools/shell.py`
- Multiple test scripts

### 2. Frontend Chat Component Refactor
- **Removed components**: `StreamingText.tsx`, `ThinkingBlock.tsx`, `ToolCallCard.tsx`
- **MessageList improvements**:
  - Added virtual list with `useVirtualList` hook for performance
  - Implemented scroll pagination with `useScrollPagination` hook
  - Added unread message count tracking
  - Improved scroll-to-bottom behavior with ref-based API
  - Better handling of message loading states
- **New hooks**: `useVirtualList`, `useScrollPagination`, `useAutoScroll`
- **New constants**: `constants/scroll.ts` with scroll configuration
- **ChatInput**: Improved model selection and UI
- **AssistantMessage**: Enhanced error handling and rendering

**Files**:
- `novaic-app/src/components/Chat/MessageList.tsx` (major refactor)
- `novaic-app/src/components/Chat/ChatInput.tsx`
- `novaic-app/src/components/Chat/AssistantMessage.tsx`
- `novaic-app/src/components/Chat/ChatPanel.tsx`
- `novaic-app/src/hooks/useVirtualList.ts` (new)
- `novaic-app/src/hooks/useScrollPagination.ts` (new)
- `novaic-app/src/hooks/useAutoScroll.ts` (new)
- `novaic-app/src/constants/scroll.ts` (new)

### 3. Backend Enum Standardization
- **New module**: `novaic-backend/common/enums.py`
  - `RuntimeStatus`: active, resting, completed, failed
  - `SubagentStatus`: sleeping, awake, summarizing, running, completed, failed, cancelled
  - `RuntimePhase`: need_think, waiting_actions, queued, thinking, tool_calling, etc.
  - `TaskState`, `SagaState`, `LogLevel`, `ExecutionLogType`
- Replaced hardcoded status strings with enum values throughout codebase
- Improved type safety and consistency

**Files**:
- `novaic-backend/common/enums.py` (new)
- `novaic-backend/gateway/api/internal.py`
- `novaic-backend/gateway/db/repositories/runtime.py`
- `novaic-backend/gateway/db/repositories/subagent.py`
- `novaic-backend/task_queue/handlers/*.py`

### 4. Runtime Summary v24 Features
- **Database schema v24**:
  - Added `subagents.hrl` (Hot Runtime List) - JSON array of runtime_ids
  - Added `subagents.summary_lock` - prevents concurrent summarization
  - Added `agent_runtimes.simple_summary` - simple runtime summary
  - Added `agent_runtimes.hot_summary` - hot summary (last 3 rounds full, rest summarized)
  - Added `agent_runtimes.cold_summary` - cold summary (all rounds summarized)
- **RuntimeRepository**: Extended to support v24 summary fields
- **SubAgentRepository**: Added HRL management methods
- **Internal API**: New endpoints for HRL operations (`/hrl`, `/hrl/add`, `/hrl/remove`)
- **Summary handlers**: New handlers for hot/cold summary generation

**Files**:
- `novaic-backend/gateway/db/schema.py` (v24 migration)
- `novaic-backend/gateway/db/repositories/runtime.py`
- `novaic-backend/gateway/db/repositories/subagent.py`
- `novaic-backend/gateway/api/internal.py` (HRL endpoints)
- `novaic-backend/task_queue/handlers/summary_handlers.py` (new)
- `novaic-backend/task_queue/sagas/summarize.py`

### 5. Configuration Management
- **New module**: `novaic-backend/common/config.py`
  - Centralized service configuration
  - Environment variable support
  - HRL configuration (trigger length, keep recent)
  - Summary configuration (last rounds full/hot)
  - Pagination configuration
  - Database transaction timeout

**Files**:
- `novaic-backend/common/config.py` (new)

### 6. Task Queue Improvements
- **Context builder**: New utility for building initial runtime context
- **Simple summary**: New utility for generating simple summaries
- **LLM handlers**: Enhanced with hot/cold summary support
- **Runtime handlers**: Improved status management with enums
- **Message handlers**: Better SubAgent status checking
- **Client improvements**: Enhanced GatewayInternalClient with new methods

**Files**:
- `novaic-backend/task_queue/utils/context_builder.py` (new)
- `novaic-backend/task_queue/utils/simple_summary.py` (new)
- `novaic-backend/task_queue/handlers/llm_handlers.py`
- `novaic-backend/task_queue/handlers/runtime_handlers.py`
- `novaic-backend/task_queue/client.py`

### 7. Frontend Store & State Management
- **Store improvements**: Better message state management
- **Types**: Removed unused types, added new message status types
- **Services**: Updated API and VM services

**Files**:
- `novaic-app/src/store/index.ts`
- `novaic-app/src/types/index.ts`
- `novaic-app/src/services/api.ts`
- `novaic-app/src/services/vm.ts`

### 8. Execution Log Improvements
- Enhanced execution log component with better rendering
- Improved log detail view
- Better error handling

**Files**:
- `novaic-app/src/components/Visual/ExecutionLog.tsx`
- `novaic-app/src/components/Visual/LogDetail.tsx` (new)

### 9. Tauri/Rust Updates
- Updated VM deployment logic
- Improved gateway client error handling
- Updated HTTP client configuration
- Icon updates

**Files**:
- `novaic-app/src-tauri/src/vm/deploy.rs`
- `novaic-app/src-tauri/src/gateway_client.rs`
- `novaic-app/src-tauri/src/http_client.rs`
- `novaic-app/src-tauri/src/main.rs`
- Icon files updated

### 10. Testing & Scripts
- Updated stress test scripts with path fixes
- Improved test configuration
- Updated conftest with cross-platform paths

**Files**:
- `novaic-backend/tests/conftest.py`
- Multiple test scripts

## Breaking Changes

None - all changes maintain backward compatibility.

## Migration Notes

- Database migration v24 will automatically add new columns
- No manual migration required for existing data
- Environment variables remain optional (defaults provided)

## Testing

- All path fixes verified on macOS
- Cross-platform compatibility maintained
- Database migrations tested
- Frontend virtual list performance verified

## Related Documentation

- `MACOS_PATH_FIX_COMPLETE.md` - Detailed path fix report
- `tech-lead-guide/frontend-scroll-patterns.md` - Frontend scroll patterns guide
- `novaic-backend/task_queue/sagas/README.md` - Saga documentation
