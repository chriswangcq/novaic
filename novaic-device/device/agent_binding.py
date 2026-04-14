"""
Helpers for device subjects, mounted tools, and runtime resolution.

Mounted tools structure: {category: [tool, ...]}

Linux VM (VMUSE):
- desktop: screenshot, mouse, keyboard
- file: pull, push
- shell: run_command
- clipboard: clipboard_get, clipboard_set

Android (mobile proxy path):
- screen: screenshot, touch, input
- file: push, pull
- shell: shell
- app: install, launch, list, stop

Host Desktop (HD — runs directly on host machine):
- desktop: screenshot, mouse, keyboard
- file: pull, push
- shell: run_command
- clipboard: clipboard_get, clipboard_set
"""

from typing import Any, Dict, List, Optional

from device.config_devices import Device, DeviceType

# Linux VM: category -> list of tool operations (VMUSE path segment)
# main desktop 可额外 mount qemu 工具
MOUNTED_TOOL_CATEGORIES: Dict[str, List[str]] = {
    "desktop": ["screenshot", "mouse", "keyboard"],
    "file": ["pull", "push"],
    "shell": ["run_command"],
    "clipboard": ["clipboard_get", "clipboard_set"],
    "qemu": ["ssh_exec", "status"],
}

# Android: category -> list of tool operations (mobile proxy path segment)
MOUNTED_TOOL_CATEGORIES_ANDROID: Dict[str, List[str]] = {
    "screen": ["screenshot", "touch", "input"],
    "file": ["push", "pull", "delete", "mkdir", "read"],
    "shell": ["shell"],
    "app": ["install", "uninstall", "launch", "list", "stop"],
    "browser": ["open", "get_url", "back", "refresh"],
    "ui": ["dump", "find", "wait", "scroll", "click_element"],
}

# Host Desktop: category -> list of tool operations
MOUNTED_TOOL_CATEGORIES_HD: Dict[str, List[str]] = {
    "desktop": ["screenshot", "mouse", "keyboard"],
    "file": ["pull", "push"],
    "shell": ["run_command"],
    "clipboard": ["clipboard_get", "clipboard_set"],
}

# VMUSE path (family, operation) -> (our category, our tool name)
PATH_TO_MOUNTED: Dict[tuple, tuple] = {
    ("desktop", "screenshot"): ("desktop", "screenshot"),
    ("desktop", "mouse"): ("desktop", "mouse"),
    ("desktop", "keyboard"): ("desktop", "keyboard"),
    ("file", "pull"): ("file", "pull"),
    ("file", "push"): ("file", "push"),
    ("shell", "run_command"): ("shell", "run_command"),
    ("shell", "command"): ("shell", "run_command"),
    ("context", "clipboard_get"): ("clipboard", "clipboard_get"),
    ("context", "clipboard_set"): ("clipboard", "clipboard_set"),
}

# Mobile proxy path -> (category, tool name)
PATH_TO_MOBILE_MOUNTED: Dict[str, tuple] = {
    "screenshot": ("screen", "screenshot"),
    "touch": ("screen", "touch"),
    "input": ("screen", "input"),
    "shell": ("shell", "shell"),
    "file/pull": ("file", "pull"),
    "file/push": ("file", "push"),
    "file/pull-content": ("file", "pull"),
    "file/push-from-base64": ("file", "push"),
    "file/delete": ("file", "delete"),
    "file/mkdir": ("file", "mkdir"),
    "file/read": ("file", "read"),
    "app/install": ("app", "install"),
    "app/uninstall": ("app", "uninstall"),
    "app/launch": ("app", "launch"),
    "app/list": ("app", "list"),
    "app/stop": ("app", "stop"),
    "app/install-from-base64": ("app", "install"),
    "browser/open": ("browser", "open"),
    "browser/get_url": ("browser", "get_url"),
    "browser/back": ("browser", "back"),
    "browser/refresh": ("browser", "refresh"),
    "ui/dump": ("ui", "dump"),
    "ui/find": ("ui", "find"),
    "ui/wait": ("ui", "wait"),
    "ui/scroll": ("ui", "scroll"),
    "ui/click_element": ("ui", "click_element"),
}

# HD proxy path (family, operation) -> (category, tool name)
PATH_TO_HD_MOUNTED: Dict[tuple, tuple] = {
    ("desktop", "screenshot"): ("desktop", "screenshot"),
    ("desktop", "mouse"): ("desktop", "mouse"),
    ("desktop", "keyboard"): ("desktop", "keyboard"),
    ("file", "pull"): ("file", "pull"),
    ("file", "push"): ("file", "push"),
    ("shell", "command"): ("shell", "run_command"),
    ("context", "clipboard_get"): ("clipboard", "clipboard_get"),
    ("context", "clipboard_set"): ("clipboard", "clipboard_set"),
}

# Tool name -> (platform, category, op) for mounted check.
# VM tools: platform="linux"; Mobile tools: platform="android"; HD tools: platform="host_desktop".
# Keys must match definitions.py t["name"] exactly.
TOOL_NAME_TO_MOUNTED: Dict[str, tuple] = {
    # VM tools needing mounted check (8 tools)
    "screenshot": ("linux", "desktop", "screenshot"),
    "mouse": ("linux", "desktop", "mouse"),
    "keyboard": ("linux", "desktop", "keyboard"),
    "file_pull": ("linux", "file", "pull"),
    "file_push": ("linux", "file", "push"),
    "shell_exec": ("linux", "shell", "run_command"),
    "clipboard_get": ("linux", "clipboard", "clipboard_get"),
    "clipboard_set": ("linux", "clipboard", "clipboard_set"),
    # QEMU tools (main desktop 可额外 mount)
    "qemu_ssh_exec": ("linux", "qemu", "ssh_exec"),
    "qemu_status": ("linux", "qemu", "status"),
    # Mobile tools (from MOBILE_TOOL_MAPPING, mapped via PATH_TO_MOBILE_MOUNTED)
    "mobile_screenshot": ("android", "screen", "screenshot"),
    "mobile_touch": ("android", "screen", "touch"),
    "mobile_input": ("android", "screen", "input"),
    "mobile_shell": ("android", "shell", "shell"),
    "mobile_app_install": ("android", "app", "install"),
    "mobile_app_uninstall": ("android", "app", "uninstall"),
    "mobile_app_launch": ("android", "app", "launch"),
    "mobile_app_list": ("android", "app", "list"),
    "mobile_app_stop": ("android", "app", "stop"),
    "mobile_browser_open": ("android", "browser", "open"),
    "mobile_browser_get_url": ("android", "browser", "get_url"),
    "mobile_browser_back": ("android", "browser", "back"),
    "mobile_browser_refresh": ("android", "browser", "refresh"),
    "mobile_ui_dump": ("android", "ui", "dump"),
    "mobile_ui_find": ("android", "ui", "find"),
    "mobile_ui_wait": ("android", "ui", "wait"),
    "mobile_ui_scroll": ("android", "ui", "scroll"),
    "mobile_ui_click_element": ("android", "ui", "click_element"),
    "mobile_file_push": ("android", "file", "push"),
    "mobile_file_pull": ("android", "file", "pull"),
    "mobile_file_delete": ("android", "file", "delete"),
    "mobile_file_mkdir": ("android", "file", "mkdir"),
    "mobile_file_read": ("android", "file", "read"),
    # HD tools (host desktop, hd_ prefix)
    "hd_screenshot": ("host_desktop", "desktop", "screenshot"),
    "hd_mouse": ("host_desktop", "desktop", "mouse"),
    "hd_keyboard": ("host_desktop", "desktop", "keyboard"),
    "hd_shell_exec": ("host_desktop", "shell", "run_command"),
    "hd_clipboard_get": ("host_desktop", "clipboard", "clipboard_get"),
    "hd_clipboard_set": ("host_desktop", "clipboard", "clipboard_set"),
    "hd_file_pull": ("host_desktop", "file", "pull"),
    "hd_file_push": ("host_desktop", "file", "push"),
}

VALID_SUBJECT_TYPES = ("main", "vm_user", "default")


def list_supported_mounted_tools() -> Dict[str, List[str]]:
    """Return category -> tools structure for Linux VM device subjects."""
    return {k: list(v) for k, v in MOUNTED_TOOL_CATEGORIES.items()}


def list_supported_mounted_tools_android() -> Dict[str, List[str]]:
    """Return category -> tools structure for Android device subjects."""
    return {k: list(v) for k, v in MOUNTED_TOOL_CATEGORIES_ANDROID.items()}


def list_supported_mounted_tools_hd() -> Dict[str, List[str]]:
    """Return category -> tools structure for Host Desktop device subjects."""
    return {k: list(v) for k, v in MOUNTED_TOOL_CATEGORIES_HD.items()}


def normalize_mounted_tools(raw: Any, device_type: Optional[str] = None) -> Dict[str, List[str]]:
    """Normalize mounted_tools from DB (supports legacy list format).
    
    When raw is a list (legacy format), device_type selects the category map:
    - "android" -> MOUNTED_TOOL_CATEGORIES_ANDROID (screen, file, shell, app, browser, ui)
    - "host_desktop" -> MOUNTED_TOOL_CATEGORIES_HD (desktop, file, shell, clipboard)
    - "linux" or None -> MOUNTED_TOOL_CATEGORIES (desktop, file, shell, clipboard)
    """
    if isinstance(raw, dict):
        return {k: list(v) if isinstance(v, list) else [] for k, v in raw.items()}
    if isinstance(raw, list):
        # Legacy: ["desktop","file",...] or ["screen","file",...] -> full selection per category
        if device_type == "android":
            categories = MOUNTED_TOOL_CATEGORIES_ANDROID
        elif device_type == "host_desktop":
            categories = MOUNTED_TOOL_CATEGORIES_HD
        else:
            categories = MOUNTED_TOOL_CATEGORIES
        return {cat: list(tools) for cat, tools in categories.items() if cat in raw}
    return {}


def is_tool_mounted(mounted: Dict[str, List[str]], path_family: str, path_op: str) -> bool:
    """Check if VMUSE path (family/op) is allowed by mounted_tools."""
    key = (path_family, path_op)
    cat, op = PATH_TO_MOUNTED.get(key, (None, None))
    if cat is None:
        return True  # Unknown path: no mounted check (e.g. browser, window)
    return op in mounted.get(cat, [])


def is_mobile_tool_mounted(mounted: Dict[str, List[str]], path: str) -> bool:
    """Check if mobile proxy path is allowed by mounted_tools (Android)."""
    cat, op = PATH_TO_MOBILE_MOUNTED.get(path, (None, None))
    if cat is None:
        return True  # Unknown path: no mounted check
    return op in mounted.get(cat, [])


def is_hd_tool_mounted(mounted: Dict[str, List[str]], path_family: str, path_op: str) -> bool:
    """Check if HD proxy path (family/op) is allowed by mounted_tools."""
    key = (path_family, path_op)
    cat, op = PATH_TO_HD_MOUNTED.get(key, (None, None))
    if cat is None:
        return True  # Unknown path: no mounted check
    return op in mounted.get(cat, [])


def list_device_subjects(device: Device) -> List[Dict[str, Any]]:
    subjects: List[Dict[str, Any]] = []

    if device.type == DeviceType.LINUX:
        subjects.append({
            "device_id": device.id,
            "device_type": device.type.value,
            "subject_type": "main",
            "subject_id": "main",
            "label": "Main Desktop",
            "desktop_resource_id": device.id,
            "linux_user": "ubuntu",
            "home_path": "/home/ubuntu",
            "supported_tools": list_supported_mounted_tools(),
        })  # supported_tools: {category: [tool, ...]}

        from device.entity_store import get_entity_store
        rows = get_entity_store().list(
            "vm-users", device.user_id or "",
            params={"device_id": device.id},
            order_by="display_num ASC",
        )
        for row in rows:
            username = row["username"]
            subjects.append({
                "device_id": device.id,
                "device_type": device.type.value,
                "subject_type": "vm_user",
                "subject_id": username,
                "label": f"Sub-user: {username}",
                "desktop_resource_id": f"{device.id}:{username}",
                "username": username,
                "display_num": row["display_num"],
                "created_at": row.get("created_at", "") or "",
                "linux_user": username,
                "home_path": f"/home/{username}",
                "supported_tools": list_supported_mounted_tools(),
            })  # supported_tools: {category: [tool, ...]}
    elif device.type == DeviceType.HOST_DESKTOP:
        subjects.append({
            "device_id": device.id,
            "device_type": device.type.value,
            "subject_type": "default",
            "subject_id": "default",
            "label": "Host Desktop",
            "desktop_resource_id": device.id,
            "supported_tools": list_supported_mounted_tools_hd(),
        })  # supported_tools: {category: [tool, ...]}
    else:
        subjects.append({
            "device_id": device.id,
            "device_type": device.type.value,
            "subject_type": "default",
            "subject_id": "default",
            "label": "Default Session",
            "desktop_resource_id": device.id,
            "android_serial": getattr(device, "device_serial", "") or "",
            "supported_tools": list_supported_mounted_tools_android(),
        })  # supported_tools: {category: [tool, ...]}

    return subjects


def get_device_subject(
    device: Device,
    subject_type: str,
    subject_id: str,
) -> Optional[Dict[str, Any]]:
    for subject in list_device_subjects(device):
        if subject["subject_type"] == subject_type and subject["subject_id"] == subject_id:
            return subject
    return None


def validate_mounted_tools(
    mounted_tools: Dict[str, List[str]],
    supported_tools: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """Validate mounted_tools against supported_tools. Returns normalized dict."""
    supported = supported_tools or {}
    result: Dict[str, List[str]] = {}
    for cat, tools in (mounted_tools or {}).items():
        if cat not in supported:
            raise ValueError(f"Unsupported category: {cat}")
        allowed = set(supported.get(cat, []))
        chosen = [t for t in tools if t in allowed]
        if chosen:
            result[cat] = sorted(set(chosen))
    return result


def build_runtime_context(device: Device, subject: Dict[str, Any]) -> Dict[str, Any]:
    runtime_context: Dict[str, Any] = {
        "device_id": device.id,
        "device_type": device.type.value,
        "device_name": device.name,
        "subject_type": subject["subject_type"],
        "subject_id": subject["subject_id"],
        "subject_label": subject["label"],
        "desktop": {
            "resource_id": subject["desktop_resource_id"],
        },
    }

    if device.type == DeviceType.LINUX:
        # display: X11 display for screenshot/mouse/keyboard. Main uses :10, vm_users use :11, :12, ...
        display_val = ":10"  # main desktop default
        if subject.get("display_num") is not None:
            display_val = f":{subject['display_num']}"
        runtime_context.update({
            "display": display_val,
            "linux_user": subject["linux_user"],
            "home_path": subject["home_path"],
            "shell": {
                "transport": "linux-user",
                "user": subject["linux_user"],
                "home_path": subject["home_path"],
            },
            "file": {
                "transport": "linux-user-home",
                "home_path": subject["home_path"],
            },
            "vm": {
                "backend": getattr(device, "backend", None),
                "ports": getattr(device, "ports", {}) or {},
            },
        })
    elif device.type == DeviceType.HOST_DESKTOP:
        import os
        runtime_context.update({
            "shell": {
                "transport": "host-shell",
            },
            "file": {
                "transport": "host-file",
                "home_path": os.path.expanduser("~"),
            },
        })
    else:
        runtime_context.update({
            "android_serial": getattr(device, "device_serial", "") or "",
            "shell": {
                "transport": "adb",
                "device_serial": getattr(device, "device_serial", "") or "",
            },
            "file": {
                "transport": "adb",
                "device_serial": getattr(device, "device_serial", "") or "",
            },
            "android": {
                "managed": getattr(device, "managed", True),
                "avd_name": getattr(device, "avd_name", "") or "",
                "device_serial": getattr(device, "device_serial", "") or "",
            },
        })

    return runtime_context


def resolve_agent_runtime_context(db, agent_id: str) -> Optional[Dict[str, Any]]:
    from device.entity_store import get_entity_store
    from device.config_devices import device_from_dict

    store = get_entity_store()

    binding_row = store.get("agent-binding", "", agent_id)
    if binding_row is None:
        return None

    device_row = store.get("devices", "", binding_row.get("device_id", ""))
    if device_row is None:
        return None
    device = device_from_dict(device_row)

    subject = get_device_subject(device, binding_row.get("subject_type", ""), binding_row.get("subject_id", ""))
    if subject is None:
        return None

    runtime_context = build_runtime_context(device, subject)
    device_type_str = (device.type.value if hasattr(device.type, "value") else str(device.type)) if getattr(device, "type", None) else None
    mounted_raw = binding_row.get("mounted_tools") or {}
    if isinstance(mounted_raw, str):
        import json
        try:
            mounted_raw = json.loads(mounted_raw)
        except (json.JSONDecodeError, TypeError):
            mounted_raw = {}
    mounted = normalize_mounted_tools(mounted_raw, device_type=device_type_str)
    device_dict = device.model_dump()
    if "type" in device_dict and hasattr(device_dict["type"], "value"):
        device_dict["type"] = device_dict["type"].value
    return {
        "binding": binding_row,
        "device": device_dict,
        "subject": subject,
        "runtime_context": runtime_context,
        "mounted_tools": mounted,
        "supported_tools": subject.get("supported_tools") or list_supported_mounted_tools(),
    }
