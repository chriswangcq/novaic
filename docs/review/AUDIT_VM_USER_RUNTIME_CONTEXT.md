# Audit: vm_user Correctness for Shell, Context, and File Tools

**Date:** 2025-03-11  
**Scope:** novaic-mcp-vmuse tools (shell.py, context.py, files.py), http_server.py routes, executor → Gateway → VMUSE flow.

---

## 1. Shell (shell_exec)

### Flow
- **Executor** → `POST /internal/agents/{agent_id}/vm/shell/command` with `json=arguments` (command, cwd, timeout, visible)
- **Gateway** (`proxy_vm_tool`) → `payload.setdefault("runtime_context", resolved.get("runtime_context"))` injects runtime_context
- **VmControl** → forwards body as-is to VM VMUSE
- **VMUSE** → `shell_run_command` extracts `_get_runtime_context(data)`, passes to `ShellTools.run_command(..., runtime_context=...)`

### Implementation
- `ShellTools._should_sudo(runtime_context)` → true when `linux_user != os.environ.get("USER")`
- `ShellTools._target_user(runtime_context)` → `runtime_context["linux_user"]`
- When sudo: `sudo -u {linux_user} -H env DISPLAY=... HOME=... bash -lc {command}`

### Verdict
**Correct.** Shell gets runtime_context with correct linux_user and uses it for sudo -u.

---

## 2. File Tools (file_pull, file_push)

### Flow
- **Executor** → `POST .../file/pull` with `json={"path": path, "binary": True}` (no runtime_context in payload)
- **Gateway** → injects `runtime_context` via `payload.setdefault(...)`
- **VMUSE** → `file_pull`/`file_push` pass `runtime_context=_get_runtime_context(data)` to `FileTools.read_file`/`write_file`

### Implementation
- `FileTools._expand_path(path, runtime_context)` → uses `home_path` for `~` and `~/...`
- `FileTools._should_sudo(runtime_context)` → true when `linux_user` present and ≠ current user
- `FileTools._run_as_user(user, ...)` → `sudo -u {user} -H python3 -c ...`

### Verdict
**Correct.** File tools use runtime_context for home_path expansion and sudo.

---

## 3. Context Tools (clipboard_get, clipboard_set, directory_snapshot, system_snapshot, etc.)

### Flow
- **Executor** → `POST .../context/{operation}` with `json=arguments`
- **Gateway** → injects `runtime_context`
- **VMUSE** → handlers call `ContextTools.*()` **without passing runtime_context**

### Gaps

| Tool | Uses runtime_context? | Needs for vm_user? | Issue |
|------|------------------------|---------------------|-------|
| **clipboard_get** | No | Yes | `xclip -selection clipboard -o` runs in process env. For vm_user, clipboard is per-X-session (DISPLAY :11, :12). Without DISPLAY=:11, xclip reads main desktop or wrong session. |
| **clipboard_set** | No | Yes | Same: xclip writes to wrong X session. |
| **directory_snapshot** | No | Yes | `Path(path).expanduser()` expands `~` to process user's home (e.g. ubuntu), not vm_user's home. Path `~/foo` for vm_user alice would resolve to `/home/ubuntu/foo` instead of `/home/alice/foo`. |
| **system_snapshot** | No | Yes | Uses `os.environ.get("USER")`, `Path.home()`, `os.getcwd()` → wrong user/home/cwd. `wmctrl -l -p` and `xclip` run without DISPLAY → wrong windows/clipboard. |
| **recent_files** | No | Yes | Same path expansion: `Path(path).expanduser()` wrong for vm_user. |
| **app_state** | No | Partial | `pgrep`, `wmctrl` may see processes/windows from wrong display. |
| **environment_info** | No | Partial | `os.environ` reflects process, not vm_user. |

### Verdict
**Gaps.** Context tools do not use runtime_context. For vm_user they will:
- Use wrong home path for `~` expansion
- Access wrong clipboard (main or empty)
- Report wrong user, home, cwd in system_snapshot
- See wrong windows (main display) in wmctrl-based calls

---

## 4. Window Tools (list_windows, focus_window, etc.)

### Flow
- **VMUSE** → handlers call `WindowTools.*()` **without runtime_context**

### Gaps
- `wmctrl -l -G`, `xdotool search` run in process env.
- For vm_user, each subuser has own Xvnc (DISPLAY :11, :12). Without `DISPLAY=:11`, wmctrl/xdotool see main desktop (:10) windows only.

### Verdict
**Gap.** Window tools do not use runtime_context; vm_user would see main desktop windows, not their own.

---

## 5. Desktop Tools (screenshot, mouse, keyboard)

### Implementation
- Use `with _patched_environ(_get_desktop_env(runtime_context)):` before calling DesktopTools
- `_get_desktop_env` sets DISPLAY, HOME, USER, LOGNAME, XDG_RUNTIME_DIR from runtime_context

### Verdict
**Correct.** Desktop tools run with patched env for vm_user.

---

## Summary of Gaps

| Category | Status | Notes |
|----------|--------|-------|
| Shell | OK | runtime_context passed, sudo -u used |
| File tools | OK | runtime_context passed, home_path + sudo |
| Desktop tools | OK | _patched_environ with runtime_context |
| **Context tools** | **Gaps** | No runtime_context; wrong home, clipboard, user for vm_user |
| **Window tools** | **Gap** | No runtime_context; wrong DISPLAY for vm_user |

---

## Recommended Fixes

1. **Context tools**
   - Add `runtime_context` parameter to `ContextTools` methods.
   - In http_server handlers, pass `runtime_context=_get_runtime_context(data)`.
   - For path-based tools (directory_snapshot, recent_files): expand `~` using `runtime_context["home_path"]` when present.
   - For clipboard_get/set: run xclip under `_patched_environ(_get_desktop_env(runtime_context))` or `sudo -u {linux_user} env DISPLAY=... xclip ...`.
   - For system_snapshot: use runtime_context for user/home; run wmctrl/xclip under patched env.

2. **Window tools**
   - In http_server handlers, wrap calls with `_patched_environ(_get_desktop_env(runtime_context))` so wmctrl/xdotool use correct DISPLAY for vm_user.
